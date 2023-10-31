# Copyright (c) Microsoft. All rights reserved.

import itertools
import os
from dataclasses import dataclass
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from numpy import ndarray
from usearch.index import (
    BatchMatches,
    CompiledMetric,
    Index,
    Matches,
    MetricKind,
    ScalarKind,
)

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


@dataclass
class _USearchCollection:
    """Represents a collection for USearch with embeddings and related data.

    Attributes:
        embeddings_index (Index): The index of embeddings.
        embeddings_data_table (pa.Table): The PyArrow table holding embeddings data.
        embeddings_id_to_label (Dict[str, int]): Mapping of embeddings ID to label.
    """

    embeddings_index: Index
    embeddings_data_table: pa.Table
    embeddings_id_to_label: Dict[str, int]

    @staticmethod
    def create_default(embeddings_index: Index) -> "_USearchCollection":
        """Create a default `_USearchCollection` using a given embeddings index.

        Args:
            embeddings_index (Index): The index of embeddings to be used for the default collection.

        Returns:
            _USearchCollection: A default `_USearchCollection` initialized with the given embeddings index.
        """
        return _USearchCollection(
            embeddings_index,
            pa.Table.from_pandas(
                pd.DataFrame(columns=_embeddings_data_schema.names),
                schema=_embeddings_data_schema,
            ),
            {},
        )


# PyArrow Schema definition for the embeddings data from `MemoryRecord`.
_embeddings_data_schema = pa.schema(
    [
        pa.field("key", pa.string()),
        pa.field("timestamp", pa.timestamp("us")),
        pa.field("is_reference", pa.bool_()),
        pa.field("external_source_name", pa.string()),
        pa.field("id", pa.string()),
        pa.field("description", pa.string()),
        pa.field("text", pa.string()),
        pa.field("additional_metadata", pa.string()),
    ]
)


class _CollectionFileType(Enum):
    """Enumeration of file types used for storing collections."""

    USEARCH = 0
    PARQUET = 1


# Mapping of collection file types to their file extensions.
_collection_file_extensions: Dict[_CollectionFileType, str] = {
    _CollectionFileType.USEARCH: ".usearch",
    _CollectionFileType.PARQUET: ".parquet",
}


def memoryrecords_to_pyarrow_table(records: List[MemoryRecord]) -> pa.Table:
    """Convert a list of `MemoryRecord` to a PyArrow Table"""
    records_pylist = [
        {attr: getattr(record, "_" + attr) for attr in _embeddings_data_schema.names}
        for record in records
    ]
    return pa.Table.from_pylist(records_pylist, schema=_embeddings_data_schema)


def pyarrow_table_to_memoryrecords(
    table: pa.Table, vectors: Optional[ndarray] = None
) -> List[MemoryRecord]:
    """Convert a PyArrow Table to a list of MemoryRecords.

    Args:
        table (pa.Table): The PyArrow Table to convert.
        vectors (Optional[ndarray], optional): An array of vectors to include as embeddings in the MemoryRecords.
            The length and order of the vectors should match the rows in the table. Defaults to None.

    Returns:
        List[MemoryRecord]: List of MemoryRecords constructed from the table.
    """
    result_memory_records = [
        MemoryRecord(
            **row.to_dict(), embedding=vectors[index] if vectors is not None else None
        )
        for index, row in table.to_pandas().iterrows()
    ]

    return result_memory_records


class USearchMemoryStore(MemoryStoreBase):
    def __init__(
        self,
        persist_directory: Optional[os.PathLike] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Create a USearchMemoryStore instance.

        This store helps searching embeddings with USearch, keeping collections in memory.
        To save collections to disk, provide the `persist_directory` param.
        Collections are saved when `close_async` is called.

        To both save collections and free up memory, call `close_async`.
        When `USearchMemoryStore` is used with a context manager, this will happen automatically.
        Otherwise, it should be called explicitly.

        Args:
            persist_directory (Optional[os.PathLike], default=None): Directory for loading and saving collections.
            If None, collections are not loaded nor saved.
            logger (Optional[Logger], default=None): Logger for diagnostics. If None, a NullLogger is used.
        """
        self._logger = logger or NullLogger()
        self._persist_directory = (
            Path(persist_directory) if persist_directory is not None else None
        )

        self._collections: Dict[str, _USearchCollection] = {}
        if self._persist_directory:
            self._collections = self._read_collections_from_dir()

    def _get_collection_path(
        self, collection_name: str, *, file_type: _CollectionFileType
    ) -> Path:
        """
        Get the path for the given collection name and file type.

        Args:
            collection_name (str): Name of the collection.
            file_type (_CollectionFileType): The file type.

        Returns:
            Path: Path to the collection file.

        Raises:
            ValueError: If persist directory path is not set.
        """
        collection_name = collection_name.lower()
        if self._persist_directory is None:
            raise ValueError("Path of persist directory is not set")

        return self._persist_directory / (
            collection_name + _collection_file_extensions[file_type]
        )

    async def create_collection_async(
        self,
        collection_name: str,
        ndim: int = 0,
        metric: Union[str, MetricKind, CompiledMetric] = MetricKind.IP,
        dtype: Optional[Union[str, ScalarKind]] = None,
        connectivity: Optional[int] = None,
        expansion_add: Optional[int] = None,
        expansion_search: Optional[int] = None,
        view: bool = False,
    ) -> None:
        """Create a new collection.

        Args:
            collection_name (str): Name of the collection. Case-insensitive.
                Must have name that is valid file name for the current OS environment.
            ndim (int, optional): Number of dimensions. Defaults to 0.
            metric (Union[str, MetricKind, CompiledMetric], optional): Metric kind. Defaults to MetricKind.IP.
            dtype (Optional[Union[str, ScalarKind]], optional): Data type. Defaults to None.
            connectivity (int, optional): Connectivity parameter. Defaults to None.
            expansion_add (int, optional): Expansion add parameter. Defaults to None.
            expansion_search (int, optional): Expansion search parameter. Defaults to None.
            view (bool, optional): Viewing flag. Defaults to False.

        Raises:
            ValueError: If collection with the given name already exists.
            ValueError: If collection name is empty string.
        """
        collection_name = collection_name.lower()
        if not collection_name:
            raise ValueError("Collection name can not be empty.")
        if collection_name in self._collections:
            raise ValueError(f"Collection with name {collection_name} already exists.")

        embeddings_index_path = (
            self._get_collection_path(
                collection_name, file_type=_CollectionFileType.USEARCH
            )
            if self._persist_directory
            else None
        )

        embeddings_index = Index(
            path=embeddings_index_path,
            ndim=ndim,
            metric=metric,
            dtype=dtype,
            connectivity=connectivity,
            expansion_add=expansion_add,
            expansion_search=expansion_search,
            view=view,
        )

        self._collections[collection_name] = _USearchCollection.create_default(
            embeddings_index
        )

        return None

    def _read_embeddings_table(
        self, path: os.PathLike
    ) -> Tuple[pa.Table, Dict[str, int]]:
        """Read embeddings from the provided path and generate an ID to label mapping.

        Args:
            path (os.PathLike): Path to the embeddings.

        Returns:
            Tuple of embeddings table and a dictionary mapping from record ID to its label.
        """
        embeddings_table = pq.read_table(path, schema=_embeddings_data_schema)
        embeddings_id_to_label: Dict[str, int] = {
            record_id: idx
            for idx, record_id in enumerate(embeddings_table.column("id").to_pylist())
        }
        return embeddings_table, embeddings_id_to_label

    def _read_embeddings_index(self, path: Path) -> Index:
        """Read embeddings index."""
        # str cast is temporarily fix for https://github.com/unum-cloud/usearch/issues/196
        return Index.restore(str(path), view=False)

    def _read_collections_from_dir(self) -> Dict[str, _USearchCollection]:
        """Read all collections from directory to memory.

        Raises:
            ValueError: If files for a collection do not match expected amount.

        Returns:
            Dict[str, _USearchCollection]: Dictionary with collection names as keys and
              their _USearchCollection as values.
        """
        collections: Dict[str, _USearchCollection] = {}

        for collection_name, collection_files in self._get_all_storage_files().items():
            expected_storage_files = len(_CollectionFileType)
            if len(collection_files) != expected_storage_files:
                raise ValueError(
                    f"Expected {expected_storage_files} files for collection {collection_name}"
                )
            parquet_file, usearch_file = collection_files
            if (
                parquet_file.suffix
                == _collection_file_extensions[_CollectionFileType.USEARCH]
            ):
                parquet_file, usearch_file = usearch_file, parquet_file

            embeddings_table, embeddings_id_to_label = self._read_embeddings_table(
                parquet_file
            )
            embeddings_index = self._read_embeddings_index(usearch_file)

            collections[collection_name] = _USearchCollection(
                embeddings_index,
                embeddings_table,
                embeddings_id_to_label,
            )

        return collections

    async def get_collections_async(self) -> List[str]:
        """Get list of existing collections.

        Returns:
            List[str]: List of collection names.
        """
        return list(self._collections.keys())

    async def delete_collection_async(self, collection_name: str) -> None:
        collection_name = collection_name.lower()
        collection = self._collections.pop(collection_name, None)
        if collection:
            collection.embeddings_index.reset()
        return None

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        collection_name = collection_name.lower()
        return collection_name in self._collections

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert single MemoryRecord and return its ID."""
        collection_name = collection_name.lower()
        res = await self.upsert_batch_async(
            collection_name=collection_name, records=[record]
        )
        return res[0]

    async def upsert_batch_async(
        self,
        collection_name: str,
        records: List[MemoryRecord],
        *,
        compact: bool = False,
        copy: bool = True,
        threads: int = 0,
        log: Union[str, bool] = False,
        batch_size: int = 0,
    ) -> List[str]:
        """Upsert a batch of MemoryRecords and return their IDs.

        Args:
            collection_name (str): Name of the collection to search within.
            records (List[MemoryRecord]): Records to upsert.
            compact (bool, optional): Removes links to removed nodes (expensive). Defaults to False.
            copy (bool, optional): Should the index store a copy of vectors. Defaults to True.
            threads (int, optional): Optimal number of cores to use. Defaults to 0.
            log (Union[str, bool], optional): Whether to print the progress bar. Defaults to False.
            batch_size (int, optional): Number of vectors to process at once. Defaults to 0.

        Raises:
            KeyError: If collection not exist

        Returns:
            List[str]: List of IDs.
        """
        collection_name = collection_name.lower()
        if collection_name not in self._collections:
            raise KeyError(
                f"Collection {collection_name} does not exist, cannot insert."
            )

        ucollection = self._collections[collection_name]
        all_records_id = [record._id for record in records]

        # Remove vectors from index
        remove_labels = [
            ucollection.embeddings_id_to_label[id]
            for id in all_records_id
            if id in ucollection.embeddings_id_to_label
        ]
        ucollection.embeddings_index.remove(
            remove_labels, compact=compact, threads=threads
        )

        # Determine label insertion points
        table_num_rows = ucollection.embeddings_data_table.num_rows
        insert_labels = np.arange(table_num_rows, table_num_rows + len(records))

        # Add embeddings to index
        ucollection.embeddings_index.add(
            keys=insert_labels,
            vectors=np.stack([record.embedding for record in records]),
            copy=copy,
            threads=threads,
            log=log,
            batch_size=batch_size,
        )

        # Update embeddings_table
        ucollection.embeddings_data_table = pa.concat_tables(
            [ucollection.embeddings_data_table, memoryrecords_to_pyarrow_table(records)]
        )

        # Update embeddings_id_to_label
        for index, record_id in enumerate(all_records_id):
            ucollection.embeddings_id_to_label[record_id] = insert_labels[index]

        return all_records_id

    async def get_async(
        self,
        collection_name: str,
        key: str,
        with_embedding: bool,
        dtype: ScalarKind = ScalarKind.F32,
    ) -> MemoryRecord:
        """Retrieve a single MemoryRecord using its key."""
        collection_name = collection_name.lower()
        result = await self.get_batch_async(
            collection_name=collection_name,
            keys=[key],
            with_embeddings=with_embedding,
            dtype=dtype,
        )
        if not result:
            raise KeyError(f"Key '{key}' not found in collection '{collection_name}'")
        return result[0]

    async def get_batch_async(
        self,
        collection_name: str,
        keys: List[str],
        with_embeddings: bool,
        dtype: ScalarKind = ScalarKind.F32,
    ) -> List[MemoryRecord]:
        """Retrieve a batch of MemoryRecords using their keys."""
        collection_name = collection_name.lower()
        if collection_name not in self._collections:
            raise KeyError(f"Collection {collection_name} does not exist")

        ucollection = self._collections[collection_name]
        labels = [
            ucollection.embeddings_id_to_label[key]
            for key in keys
            if key in ucollection.embeddings_id_to_label
        ]
        if not labels:
            return []
        vectors = (
            ucollection.embeddings_index.get_vectors(labels, dtype)
            if with_embeddings
            else None
        )

        return pyarrow_table_to_memoryrecords(
            ucollection.embeddings_data_table.take(pa.array(labels)), vectors
        )

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Remove a single MemoryRecord using its key."""
        collection_name = collection_name.lower()
        await self.remove_batch_async(collection_name=collection_name, keys=[key])
        return None

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Remove a batch of MemoryRecords using their keys."""
        collection_name = collection_name.lower()
        if collection_name not in self._collections:
            raise KeyError(
                f"Collection {collection_name} does not exist, cannot insert."
            )

        ucollection = self._collections[collection_name]

        labels = [ucollection.embeddings_id_to_label[key] for key in keys]
        ucollection.embeddings_index.remove(labels)
        for key in keys:
            del ucollection.embeddings_id_to_label[key]

        return None

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = True,
        exact: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """Retrieve the nearest matching MemoryRecord for the provided embedding.

        By default it is approximately search, see `exact` param description.

        Measure of similarity between vectors is relevance score. It is from 0 to 1.
        USearch returns distances for vectors. Distance is converted to relevance score by inverse function.

        Args:
            collection_name (str): Name of the collection to search within.
            embedding (ndarray): The embedding vector to search for.
            min_relevance_score (float, optional): The minimum relevance score for vectors. Supposed to be from 0 to 1.
                Only vectors with greater or equal relevance score are returned. Defaults to 0.0.
            with_embedding (bool, optional): If True, include the embedding in the result. Defaults to True.
            exact (bool, optional): Perform exhaustive linear-time exact search. Defaults to False.

        Returns:
            Tuple[MemoryRecord, float]: The nearest matching record and its relevance score.
        """
        collection_name = collection_name.lower()
        results = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
            exact=exact,
        )
        return results[0]

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = True,
        *,
        threads: int = 0,
        exact: bool = False,
        log: Union[str, bool] = False,
        batch_size: int = 0,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Get the nearest matches to a given embedding.

        By default it is approximately search, see `exact` param description.

        Measure of similarity between vectors is relevance score. It is from 0 to 1.
        USearch returns distances for vectors. Distance is converted to relevance score by inverse function.

        Args:
            collection_name (str): Name of the collection to search within.
            embedding (ndarray): The embedding vector to search for.
            limit (int): maximum amount of embeddings to search for.
            min_relevance_score (float, optional): The minimum relevance score for vectors. Supposed to be from 0 to 1.
                Only vectors with greater or equal relevance score are returned. Defaults to 0.0.
            with_embedding (bool, optional): If True, include the embedding in the result. Defaults to True.
            threads (int, optional): Optimal number of cores to use. Defaults to 0.
            exact (bool, optional): Perform exhaustive linear-time exact search. Defaults to False.
            log (Union[str, bool], optional): Whether to print the progress bar. Defaults to False.
            batch_size (int, optional): Number of vectors to process at once. Defaults to 0.

        Raises:
            KeyError: if a collection with specified name does not exist

        Returns:
            List[Tuple[MemoryRecord, float]]: The nearest matching records and their relevance score.
        """
        collection_name = collection_name.lower()
        ucollection = self._collections[collection_name]

        result: Union[Matches, BatchMatches] = ucollection.embeddings_index.search(
            vectors=embedding,
            k=limit,
            threads=threads,
            exact=exact,
            log=log,
            batch_size=batch_size,
        )

        assert isinstance(result, Matches)

        relevance_score = 1 / (result.distances + 1)
        filtered_labels = result.keys[
            np.where(relevance_score >= min_relevance_score)[0]
        ]

        filtered_vectors: Optional[np.ndarray] = None
        if with_embeddings:
            filtered_vectors = ucollection.embeddings_index.get_vectors(filtered_labels)

        return [
            (mem_rec, relevance_score[index].item())
            for index, mem_rec in enumerate(
                pyarrow_table_to_memoryrecords(
                    ucollection.embeddings_data_table.take(pa.array(filtered_labels)),
                    filtered_vectors,
                )
            )
        ]

    def _get_all_storage_files(self) -> Dict[str, List[Path]]:
        """Return storage files for each collection in `self._persist_directory`.

        Collection name is derived from file name and converted to lowercase. Files with extensions that
        do not match storage extensions are discarded.

        Raises:
            ValueError: If persist directory is not set.

        Returns:
            Dict[str, List[Path]]: Dictionary of collection names mapped to their respective files.
        """
        if self._persist_directory is None:
            raise ValueError("Persist directory is not set")

        storage_exts = _collection_file_extensions.values()
        collection_storage_files: Dict[str, List[Path]] = {}
        for path in self._persist_directory.iterdir():
            if path.is_file() and (path.suffix in storage_exts):
                collection_name = path.stem.lower()
                if collection_name in collection_storage_files:
                    collection_storage_files[collection_name].append(path)
                else:
                    collection_storage_files[collection_name] = [path]
        return collection_storage_files

    def _dump_collections(self) -> None:
        collection_storage_files = self._get_all_storage_files()
        for file_path in itertools.chain.from_iterable(
            collection_storage_files.values()
        ):
            file_path.unlink()

        for collection_name, ucollection in self._collections.items():
            ucollection.embeddings_index.save(
                self._get_collection_path(
                    collection_name, file_type=_CollectionFileType.USEARCH
                )
            )
            pq.write_table(
                ucollection.embeddings_data_table,
                self._get_collection_path(
                    collection_name, file_type=_CollectionFileType.PARQUET
                ),
            )

        return None

    async def close_async(self) -> None:
        """Persist collection, clear.

        Returns:
            None
        """
        if self._persist_directory:
            self._dump_collections()

        for collection_name in await self.get_collections_async():
            await self.delete_collection_async(collection_name)
        self._collections = {}
