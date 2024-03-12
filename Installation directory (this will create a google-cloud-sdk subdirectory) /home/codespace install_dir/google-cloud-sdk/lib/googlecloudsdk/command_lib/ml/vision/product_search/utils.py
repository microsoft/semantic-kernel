# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for ml vision product search surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.ml.vision import api_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.console import console_io


class Error(core_exceptions.Error):
  """Base Error for this Module."""


class LabelsFormatError(Error):
  """Raises when labels are not formatted correctly."""


def ProductLabelsArgumentsForCreate():
  return [
      base.Argument(
          '--product-labels',
          metavar='KEY=VALUE',
          type=arg_parsers.ArgList(min_length=1, element_type=str),
          action='append',
          help="""\
          Labels that can be attached to the product. Labels are specified as
          key-value pairs. Multiple values can be assigned to the same key and
          one product may have up to 100 product labels.""")
  ]


def GetClearLabelsFlag(labels_name='product-labels'):
  return base.Argument(
      '--clear-{labels}'.format(labels=labels_name),
      action='store_true',
      help="""\
          Remove all product labels. If `--add-{labels}` is also specified, then
          `--clear-{labels}` is applied first.

          For example, to remove all product labels:

              $ {{command}} --clear-{labels}

          To set the product labels to exactly "foo" and "baz":

              $ {{command}} --clear-{labels} --add-{labels}='foo=bar,baz=qux'
          """.format(labels=labels_name))


def GetRemoveLabelsFlag(labels_name='product-labels'):
  return base.Argument(
      '--remove-{labels}'.format(labels=labels_name),
      metavar='KEY=VALUE',
      type=arg_parsers.ArgList(),
      action='append',
      help="""\
          List of product labels to remove. If `--add-{labels}` is also
          specified, then `--remove-{labels}` is applied first. If a label does
          not exist it is silently ignored. Because each key can be associated
          with multiple values, both key and value need to be specified to
          remove the product label.

          For example, to remove the product labels 'foo=baz' and 'baz=qux':

              $ {{command}} --remove-{labels}='foo=baz,baz=qux'
          """.format(labels=labels_name))


def GetAddLabelsFlag(labels_name='product-labels'):
  return base.Argument(
      '--add-{}'.format(labels_name),
      metavar='KEY=VALUE',
      type=arg_parsers.ArgList(),
      action='append',
      help="""\
          List of product labels to add. If a label already exists, it is
          silently ignored.

          For example, to add the product labels 'foo=baz' and 'baz=qux':

              $ {{command}} --add-{labels}='foo=baz,baz=qux'

          To change the product label 'foo=baz' to 'foo=qux':

              $ {{command}} --remove-{labels}='foo=baz' --add-{labels}='foo-qux'
          """.format(labels=labels_name))


def ProductLabelsArgumentsForUpdate():
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(GetClearLabelsFlag())
  remove_group.AddArgument(GetRemoveLabelsFlag())
  return [GetAddLabelsFlag(), remove_group]


def _FormatLabelsArgsToKeyValuePairs(labels):
  """Flattens the labels specified in cli to a list of (k, v) pairs."""
  labels = [] if labels is None else labels

  labels_flattened = []
  for labels_sublist in labels:
    labels_flattened.extend([label.strip() for label in labels_sublist])
  labels_flattened_unique = list(set(labels_flattened))
  return [_ExtractKeyValueFromLabel(label) for label in labels_flattened_unique]


def _FormatKeyValuePairsToLabelsMessage(labels):
  """Converts the list of (k, v) pairs into labels API message."""
  sorted_labels = sorted(labels, key=lambda x: x[0] + x[1])
  return [
      api_utils.GetMessage().KeyValue(key=k, value=v) for k, v in sorted_labels
  ]


def _ExtractKeyValuePairsFromLabelsMessage(labels):
  """Extracts labels as a list of (k, v) pairs from the labels API message."""
  labels = [] if labels is None else labels
  return [(label.key, label.value) for label in labels]


def _ExtractKeyValueFromLabel(label):
  """Extracts key and value from label like 'key=value'.

  Args:
    label: str, the label to extract key and values, i.e. 'foo=buz'.

  Returns:
    (k, v): k is the substring before '=', v is the substring after '='.

  Raises:
    LabelsFormatError, raises when label is not formatted as 'key=value', or
    key or value is empty.
  """
  try:
    k, v = label.split('=')
    if k and v:
      return k, v
    raise ValueError('Key or value cannot be empty string.')
  except ValueError:
    raise LabelsFormatError('Each label must be formatted as "key=value".'
                            ' key and value cannot be empty.')


def PrepareProductLabelsForProductCreationRequest(ref, args, request):
  """Sets labels if user specifies the --product-labels in product creation."""
  del ref  # Unused
  if not args.IsSpecified('product_labels'):
    return request
  else:
    labels = _FormatLabelsArgsToKeyValuePairs(args.product_labels)
    request.product.productLabels = _FormatKeyValuePairsToLabelsMessage(labels)
    return request


def _ClearLabels(existing_labels):
  del existing_labels  # Unused
  return []


def _RemoveLabels(existing_labels, labels_to_remove):
  """Removes labels in labels_to_remove from existing_labels.

  Args:
    existing_labels: list of (k,v) pairs, existing labels.
    labels_to_remove: list of (k, v) pairs, labels to remove.

  Returns:
    List of remaining labels after removal.
  """
  return [label for label in existing_labels if label not in labels_to_remove]


def _AddLabels(existing_labels, labels_to_add):
  """Adds labels in labels_to_add to existing_labels."""
  updated_labels = existing_labels + labels_to_add
  return list(set(updated_labels))


def _LabelsUpdated(existing_labels, updated_labels):
  return set(existing_labels) != set(updated_labels)


def _AddFieldToUpdateMask(field, patch_request):
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def _GetExistingProductLabels(product_ref):
  """Fetches the existing product labels to update."""
  get_request_message = api_utils.GetMessage(
  ).VisionProjectsLocationsProductsGetRequest(name=product_ref.RelativeName())
  product = api_utils.GetClient().projects_locations_products.Get(
      get_request_message)
  return product.productLabels


def UpdateLabelsAndUpdateMaskForProductUpdateRequest(product_ref, args,
                                                     patch_request):
  """Updates product labels field."""

  if not args.IsSpecified('add_product_labels') and not args.IsSpecified(
      'remove_product_labels') and not args.IsSpecified('clear_product_labels'):
    return patch_request

  existing_labels = _GetExistingProductLabels(product_ref)

  existing_labels = _ExtractKeyValuePairsFromLabelsMessage(existing_labels)
  existing_labels_copy = copy.deepcopy(existing_labels)

  if args.clear_product_labels:
    existing_labels = _ClearLabels(existing_labels)
  if args.remove_product_labels:
    labels_to_remove = _FormatLabelsArgsToKeyValuePairs(
        args.remove_product_labels)
    existing_labels = _RemoveLabels(existing_labels, labels_to_remove)
  if args.add_product_labels:
    labels_to_add = _FormatLabelsArgsToKeyValuePairs(args.add_product_labels)
    existing_labels = _AddLabels(existing_labels, labels_to_add)

  if _LabelsUpdated(existing_labels, existing_labels_copy):
    patch_request = _AddFieldToUpdateMask('productLabels', patch_request)
    updated_labels_message = _FormatKeyValuePairsToLabelsMessage(
        existing_labels)
    if patch_request.product is None:
      patch_request.product = api_utils.GetMessage().Product()
    patch_request.product.productLabels = updated_labels_message

  return patch_request


def AddBoundingPolygonsArg():
  return [
      base.Argument(
          '--bounding-polygon',
          type=arg_parsers.ArgDict(
              spec={
                  'vertices': list,
                  'normalized-vertices': list
              },
              min_length=1),
          action='append',
          help="""\
      Bounding polygon around the areas of interest in the reference image.
      If this field is empty, the system will try to detect regions of interest.
      This flag is repeatable to specify multiple bounding polygons. At most 10
      bounding polygons will be used.

      A bounding polygon can be specified by a list of vertices or normalized
      vertices or both. A vertex (x, y) represents a 2D point in the image. x, y
      are integers and are in the same scale as the original image.
      The normalized vertex coordinates are relative to original image and
      range from 0 to 1.

      Because of the complexity of this flag, it should be specified
      with the `--flags-file`. See $ gcloud topic flags-file for details.
      See the examples section for how to use `--bounding-polygon` in
      `--flags-file`.""")
  ]


def AddBoundingPolygonsToReferenceImageCreationRequest(ref, args, request):
  """Populate the boundingPolygon message."""
  del ref  # Unused
  if not args.IsSpecified('bounding_polygon'):
    return request

  bounding_polygon_message = []
  for bounding_polygon in args.bounding_polygon:
    bounding_polygon_message.append(
        _PrepareBoundingPolygonMessage(bounding_polygon))
  request.referenceImage.boundingPolys = bounding_polygon_message
  return request


def _PrepareBoundingPolygonMessage(bounding_polygon):
  """Prepares the bounding polygons message given user's input."""
  bounding_polygon_message = api_utils.GetMessage().BoundingPoly()
  vertices_message = []
  normalized_vertices_message = []
  if 'vertices' in bounding_polygon:
    for vertex in bounding_polygon['vertices']:
      vertex_int = Vertex(vertex['x'], vertex['y'])
      vertices_message.append(api_utils.GetMessage().Vertex(
          x=vertex_int.x, y=vertex_int.y))
  if 'normalized-vertices' in bounding_polygon:
    for normalized_vertex in bounding_polygon['normalized-vertices']:
      normalized_vertex_float = NormalizedVertex(normalized_vertex['x'],
                                                 normalized_vertex['y'])
      normalized_vertices_message.append(
          api_utils.GetMessage().NormalizedVertex(
              x=normalized_vertex_float.x, y=normalized_vertex_float.y))
  bounding_polygon_message.vertices = vertices_message
  bounding_polygon_message.normalizedVertices = normalized_vertices_message
  return bounding_polygon_message


class BoundingPolygonFormatError(Error):
  """Raises when the specified polygon is incorrect."""


class VertexFormatError(BoundingPolygonFormatError):
  """Raises when the vertex is not specified correctly."""


class NormalizedVertexFormatError(BoundingPolygonFormatError):
  """Raises when the normalized vertex is not specified correctly."""


class Vertex(object):
  """Vertex to define the polygon.

  Attributes:
     x: int, x coordinate of a point on a image.
     y: int, y coordinate of a point on a image.
  """

  def __init__(self, x, y):
    self.x = _ValidateAndConvertCoordinateToInteger(x)
    self.y = _ValidateAndConvertCoordinateToInteger(y)


def _ValidateAndConvertCoordinateToInteger(coordinate):
  try:
    coordinate_int = int(coordinate)
    if coordinate_int < 0:
      raise ValueError
  except ValueError:
    raise VertexFormatError('Coordinates must be non-negative integers.')
  return coordinate_int


class NormalizedVertex(object):
  """Normalized Vertex to define the polygon.

  Attributes:
     x: float, a float from 0 to 1, inclusive. x coordinate of a point on a
       image.
     y: float, a float from 0 to 1, inclusive. y coordinate of a point on a
       image.
  """

  def __init__(self, x, y):
    self.x = _ValidateAndConvertCoordinateToFloat(x)
    self.y = _ValidateAndConvertCoordinateToFloat(y)


def _ValidateAndConvertCoordinateToFloat(coordinate):
  try:
    coordinate_float = float(coordinate)
    if coordinate_float < 0 or coordinate_float > 1:
      raise ValueError
  except ValueError:
    raise NormalizedVertexFormatError(
        'Coordinates must be floats from 0 to 1, inclusive')
  return coordinate_float


def FixOperationNameInGetOperationRequest(ref, args, request):
  del ref, args  # Unused
  name = request.name
  if name.count('operations') == 2 and name.startswith('operations/'):
    name = name[len('operations/'):]
  request.name = name
  return request


def _GetProductFullName(ref, args):
  return 'projects/{}/locations/{}/products/{}'.format(
      ref.projectsId, ref.locationsId, args.product)


def FixProductInAddProductToProductSetRequest(ref, args, request):
  """Sets product field to the full name of the product."""
  product_name = _GetProductFullName(ref, args)
  request.addProductToProductSetRequest.product = product_name
  return request


def FixProductInRemoveProductFromProductSetRequest(ref, args, request):
  """Sets product field to the full name of the product."""
  product_name = _GetProductFullName(ref, args)
  request.removeProductFromProductSetRequest.product = product_name
  return request


def FixNameInListProductsInProductSetRequest(ref, args, request):
  """Removes the redundant suffix."""
  del ref, args  # Unused
  name = request.name
  if name[-9:] == '/products':
    name = name[:-9]
  request.name = name
  return request


def _LocationAttributeConfig(name='location'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The location of the {resource}.')


def _ProductSetAttributeConfig(name='product-set'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The product set for the {resource}.')


def _GetProductSetResourceSpec(resource_name='product set'):
  return concepts.ResourceSpec(
      'vision.projects.locations.productSets',
      resource_name=resource_name,
      productSetsId=_ProductSetAttributeConfig(),
      locationsId=_LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def _GetProductSetConcept():
  return concept_parsers.ConceptParser.ForResource(
      '--product-set',
      _GetProductSetResourceSpec(),
      'The product set to be searched for similar images.',
      required=True,
      prefixes=True)


def ProductSetArgsForDetectProduct():
  return [_GetProductSetConcept()]


def AddProductSetToDetectProductRequest(ref, args, request):
  """Adds productSet field to the detect product request."""
  del ref  # Unused
  try:
    single_request = request.requests[0]
  except IndexError:
    return request
  product_set_ref = args.CONCEPTS.product_set.Parse()
  product_set_name = product_set_ref.RelativeName()
  single_request = _InstantiateProductSearchParams(single_request)
  single_request.imageContext.productSearchParams.productSet = product_set_name
  return request


def AddBoundingPolygonToDetectProductRequest(ref, args, request):
  """Adds the boundingPoly field to detect product request."""
  del ref  # Unused
  try:
    single_request = request.requests[0]
  except IndexError:
    return request
  if not args.IsSpecified('bounding_polygon'):
    return request
  polygon = _ValidateAndExtractFromBoundingPolygonArgs(args.bounding_polygon)
  if not polygon:
    return request
  single_request = _InstantiateProductSearchParams(single_request)
  product_search_params = single_request.imageContext.productSearchParams
  if not product_search_params.boundingPoly:
    product_search_params.boundingPoly = api_utils.GetMessage().BoundingPoly()
  bounding_poly = product_search_params.boundingPoly

  if isinstance(polygon[0], Vertex):
    vertices = [api_utils.GetMessage().Vertex(x=v.x, y=v.y) for v in polygon]
    bounding_poly.vertices = vertices
  else:
    normalized_vertices = [
        api_utils.GetMessage().NormalizedVertex(x=v.x, y=v.y) for v in polygon
    ]
    bounding_poly.normalizedVertices = normalized_vertices
  return request


def _InstantiateProductSearchParams(request):
  if not request.imageContext:
    request.imageContext = api_utils.GetMessage().ImageContext()
  if not request.imageContext.productSearchParams:
    request.imageContext.productSearchParams = api_utils.GetMessage(
    ).ProductSearchParams()
  return request


def _ValidateAndExtractFromBoundingPolygonArgs(bounding_polygon_arg):
  """Extracts coordinates from users' input."""
  if not bounding_polygon_arg:
    return []

  coordinates = bounding_polygon_arg.split(',')
  grouped_coordinates = GroupCoordinates(coordinates)

  if _IsPolygonSpecifiedAsVertex(coordinates):
    return [Vertex(x, y) for x, y in grouped_coordinates]
  if _IsPolygonSpecifiedAsNormalizedVertex(coordinates):
    return [NormalizedVertex(x, y) for x, y in grouped_coordinates]

  raise BoundingPolygonFormatError(
      'Coordinates of normalized vertex should have decimal points, '
      'Coordinates of vertex should be integers and cannot have decimal points.'
  )


def GroupCoordinates(coordinates):
  if len(coordinates) % 2 != 0:
    raise BoundingPolygonFormatError(
        'There must be an even number of values in the list.')
  grouped_coordinates = []
  for i in range(0, len(coordinates), 2):
    grouped_coordinates.append((coordinates[i], coordinates[i + 1]))
  return grouped_coordinates


def _IsPolygonSpecifiedAsVertex(bounding_polygon_coordinates):
  coordinate_with_decimal_point = [
      c for c in bounding_polygon_coordinates if '.' in c
  ]
  return not coordinate_with_decimal_point


def _IsPolygonSpecifiedAsNormalizedVertex(bounding_polygon_coordinates):
  coordinate_with_decimal_point = [
      c for c in bounding_polygon_coordinates if '.' in c
  ]
  return len(coordinate_with_decimal_point) == len(bounding_polygon_coordinates)


def PromptDeleteAll(ref, args, request):
  """Prompts to confirm deletion. Changes orphan-products to None if False."""
  del ref
  if not args.force:
    console_io.PromptContinue(
        message=('You are about to delete products. After deletion, the '
                 'products cannot be restored.'),
        cancel_on_no=True)
    request.purgeProductsRequest.force = True
    # because deleteOrphanProducts is boolean, if it isn't declared, it will
    # have a value of False instead of None
  if args.product_set:
    request.purgeProductsRequest.deleteOrphanProducts = None

  return request
