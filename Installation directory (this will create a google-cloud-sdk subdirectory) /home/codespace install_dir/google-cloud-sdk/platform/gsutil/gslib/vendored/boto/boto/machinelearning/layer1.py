# Copyright (c) 2015 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

import boto
from boto.compat import json, urlsplit
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.machinelearning import exceptions


class MachineLearningConnection(AWSQueryConnection):
    """
    Definition of the public APIs exposed by Amazon Machine Learning
    """
    APIVersion = "2014-12-12"
    AuthServiceName = 'machinelearning'
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "machinelearning.us-east-1.amazonaws.com"
    ServiceName = "MachineLearning"
    TargetPrefix = "AmazonML_20141212"
    ResponseError = JSONResponseError

    _faults = {
        "InternalServerException": exceptions.InternalServerException,
        "LimitExceededException": exceptions.LimitExceededException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "IdempotentParameterMismatchException": exceptions.IdempotentParameterMismatchException,
        "PredictorNotMountedException": exceptions.PredictorNotMountedException,
        "InvalidInputException": exceptions.InvalidInputException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(MachineLearningConnection, self).__init__(**kwargs)
        self.region = region
        self.auth_region_name = self.region.name

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_batch_prediction(self, batch_prediction_id, ml_model_id,
                                batch_prediction_data_source_id, output_uri,
                                batch_prediction_name=None):
        """
        Generates predictions for a group of observations. The
        observations to process exist in one or more data files
        referenced by a `DataSource`. This operation creates a new
        `BatchPrediction`, and uses an `MLModel` and the data files
        referenced by the `DataSource` as information sources.

        `CreateBatchPrediction` is an asynchronous operation. In
        response to `CreateBatchPrediction`, Amazon Machine Learning
        (Amazon ML) immediately returns and sets the `BatchPrediction`
        status to `PENDING`. After the `BatchPrediction` completes,
        Amazon ML sets the status to `COMPLETED`.

        You can poll for status updates by using the
        GetBatchPrediction operation and checking the `Status`
        parameter of the result. After the `COMPLETED` status appears,
        the results are available in the location specified by the
        `OutputUri` parameter.

        :type batch_prediction_id: string
        :param batch_prediction_id: A user-supplied ID that uniquely identifies
            the `BatchPrediction`.

        :type batch_prediction_name: string
        :param batch_prediction_name: A user-supplied name or description of
            the `BatchPrediction`. `BatchPredictionName` can only use the UTF-8
            character set.

        :type ml_model_id: string
        :param ml_model_id: The ID of the `MLModel` that will generate
            predictions for the group of observations.

        :type batch_prediction_data_source_id: string
        :param batch_prediction_data_source_id: The ID of the `DataSource` that
            points to the group of observations to predict.

        :type output_uri: string
        :param output_uri: The location of an Amazon Simple Storage Service
            (Amazon S3) bucket or directory to store the batch prediction
            results. The following substrings are not allowed in the s3 key
            portion of the "outputURI" field: ':', '//', '/./', '/../'.
        Amazon ML needs permissions to store and retrieve the logs on your
            behalf. For information about how to set permissions, see the
            `Amazon Machine Learning Developer Guide`_.

        """
        params = {
            'BatchPredictionId': batch_prediction_id,
            'MLModelId': ml_model_id,
            'BatchPredictionDataSourceId': batch_prediction_data_source_id,
            'OutputUri': output_uri,
        }
        if batch_prediction_name is not None:
            params['BatchPredictionName'] = batch_prediction_name
        return self.make_request(action='CreateBatchPrediction',
                                 body=json.dumps(params))

    def create_data_source_from_rds(self, data_source_id, rds_data, role_arn,
                                    data_source_name=None,
                                    compute_statistics=None):
        """
        Creates a `DataSource` object from an ` Amazon Relational
        Database Service`_ (Amazon RDS). A `DataSource` references
        data that can be used to perform CreateMLModel,
        CreateEvaluation, or CreateBatchPrediction operations.

        `CreateDataSourceFromRDS` is an asynchronous operation. In
        response to `CreateDataSourceFromRDS`, Amazon Machine Learning
        (Amazon ML) immediately returns and sets the `DataSource`
        status to `PENDING`. After the `DataSource` is created and
        ready for use, Amazon ML sets the `Status` parameter to
        `COMPLETED`. `DataSource` in `COMPLETED` or `PENDING` status
        can only be used to perform CreateMLModel, CreateEvaluation,
        or CreateBatchPrediction operations.

        If Amazon ML cannot accept the input source, it sets the
        `Status` parameter to `FAILED` and includes an error message
        in the `Message` attribute of the GetDataSource operation
        response.

        :type data_source_id: string
        :param data_source_id: A user-supplied ID that uniquely identifies the
            `DataSource`. Typically, an Amazon Resource Number (ARN) becomes
            the ID for a `DataSource`.

        :type data_source_name: string
        :param data_source_name: A user-supplied name or description of the
            `DataSource`.

        :type rds_data: dict
        :param rds_data:
        The data specification of an Amazon RDS `DataSource`:


        + DatabaseInformation -

            + `DatabaseName ` - Name of the Amazon RDS database.
            + ` InstanceIdentifier ` - Unique identifier for the Amazon RDS
                  database instance.

        + DatabaseCredentials - AWS Identity and Access Management (IAM)
              credentials that are used to connect to the Amazon RDS database.
        + ResourceRole - Role (DataPipelineDefaultResourceRole) assumed by an
              Amazon Elastic Compute Cloud (EC2) instance to carry out the copy
              task from Amazon RDS to Amazon S3. For more information, see `Role
              templates`_ for data pipelines.
        + ServiceRole - Role (DataPipelineDefaultRole) assumed by the AWS Data
              Pipeline service to monitor the progress of the copy task from
              Amazon RDS to Amazon Simple Storage Service (S3). For more
              information, see `Role templates`_ for data pipelines.
        + SecurityInfo - Security information to use to access an Amazon RDS
              instance. You need to set up appropriate ingress rules for the
              security entity IDs provided to allow access to the Amazon RDS
              instance. Specify a [ `SubnetId`, `SecurityGroupIds`] pair for a
              VPC-based Amazon RDS instance.
        + SelectSqlQuery - Query that is used to retrieve the observation data
              for the `Datasource`.
        + S3StagingLocation - Amazon S3 location for staging RDS data. The data
              retrieved from Amazon RDS using `SelectSqlQuery` is stored in this
              location.
        + DataSchemaUri - Amazon S3 location of the `DataSchema`.
        + DataSchema - A JSON string representing the schema. This is not
              required if `DataSchemaUri` is specified.
        + DataRearrangement - A JSON string representing the splitting
              requirement of a `Datasource`. Sample - ` "{\"randomSeed\":\"some-
              random-seed\",
              \"splitting\":{\"percentBegin\":10,\"percentEnd\":60}}"`

        :type role_arn: string
        :param role_arn: The role that Amazon ML assumes on behalf of the user
            to create and activate a data pipeline in the users account and
            copy data (using the `SelectSqlQuery`) query from Amazon RDS to
            Amazon S3.

        :type compute_statistics: boolean
        :param compute_statistics: The compute statistics for a `DataSource`.
            The statistics are generated from the observation data referenced
            by a `DataSource`. Amazon ML uses the statistics internally during
            an `MLModel` training. This parameter must be set to `True` if the
            ``DataSource `` needs to be used for `MLModel` training.

        """
        params = {
            'DataSourceId': data_source_id,
            'RDSData': rds_data,
            'RoleARN': role_arn,
        }
        if data_source_name is not None:
            params['DataSourceName'] = data_source_name
        if compute_statistics is not None:
            params['ComputeStatistics'] = compute_statistics
        return self.make_request(action='CreateDataSourceFromRDS',
                                 body=json.dumps(params))

    def create_data_source_from_redshift(self, data_source_id, data_spec,
                                         role_arn, data_source_name=None,
                                         compute_statistics=None):
        """
        Creates a `DataSource` from `Amazon Redshift`_. A `DataSource`
        references data that can be used to perform either
        CreateMLModel, CreateEvaluation or CreateBatchPrediction
        operations.

        `CreateDataSourceFromRedshift` is an asynchronous operation.
        In response to `CreateDataSourceFromRedshift`, Amazon Machine
        Learning (Amazon ML) immediately returns and sets the
        `DataSource` status to `PENDING`. After the `DataSource` is
        created and ready for use, Amazon ML sets the `Status`
        parameter to `COMPLETED`. `DataSource` in `COMPLETED` or
        `PENDING` status can only be used to perform CreateMLModel,
        CreateEvaluation, or CreateBatchPrediction operations.

        If Amazon ML cannot accept the input source, it sets the
        `Status` parameter to `FAILED` and includes an error message
        in the `Message` attribute of the GetDataSource operation
        response.

        The observations should exist in the database hosted on an
        Amazon Redshift cluster and should be specified by a
        `SelectSqlQuery`. Amazon ML executes ` Unload`_ command in
        Amazon Redshift to transfer the result set of `SelectSqlQuery`
        to `S3StagingLocation.`

        After the `DataSource` is created, it's ready for use in
        evaluations and batch predictions. If you plan to use the
        `DataSource` to train an `MLModel`, the `DataSource` requires
        another item -- a recipe. A recipe describes the observation
        variables that participate in training an `MLModel`. A recipe
        describes how each input variable will be used in training.
        Will the variable be included or excluded from training? Will
        the variable be manipulated, for example, combined with
        another variable or split apart into word combinations? The
        recipe provides answers to these questions. For more
        information, see the Amazon Machine Learning Developer Guide.

        :type data_source_id: string
        :param data_source_id: A user-supplied ID that uniquely identifies the
            `DataSource`.

        :type data_source_name: string
        :param data_source_name: A user-supplied name or description of the
            `DataSource`.

        :type data_spec: dict
        :param data_spec:
        The data specification of an Amazon Redshift `DataSource`:


        + DatabaseInformation -

            + `DatabaseName ` - Name of the Amazon Redshift database.
            + ` ClusterIdentifier ` - Unique ID for the Amazon Redshift cluster.

        + DatabaseCredentials - AWS Identity abd Access Management (IAM)
              credentials that are used to connect to the Amazon Redshift
              database.
        + SelectSqlQuery - Query that is used to retrieve the observation data
              for the `Datasource`.
        + S3StagingLocation - Amazon Simple Storage Service (Amazon S3)
              location for staging Amazon Redshift data. The data retrieved from
              Amazon Relational Database Service (Amazon RDS) using
              `SelectSqlQuery` is stored in this location.
        + DataSchemaUri - Amazon S3 location of the `DataSchema`.
        + DataSchema - A JSON string representing the schema. This is not
              required if `DataSchemaUri` is specified.
        + DataRearrangement - A JSON string representing the splitting
              requirement of a `Datasource`. Sample - ` "{\"randomSeed\":\"some-
              random-seed\",
              \"splitting\":{\"percentBegin\":10,\"percentEnd\":60}}"`

        :type role_arn: string
        :param role_arn: A fully specified role Amazon Resource Name (ARN).
            Amazon ML assumes the role on behalf of the user to create the
            following:


        + A security group to allow Amazon ML to execute the `SelectSqlQuery`
              query on an Amazon Redshift cluster
        + An Amazon S3 bucket policy to grant Amazon ML read/write permissions
              on the `S3StagingLocation`

        :type compute_statistics: boolean
        :param compute_statistics: The compute statistics for a `DataSource`.
            The statistics are generated from the observation data referenced
            by a `DataSource`. Amazon ML uses the statistics internally during
            `MLModel` training. This parameter must be set to `True` if the
            ``DataSource `` needs to be used for `MLModel` training

        """
        params = {
            'DataSourceId': data_source_id,
            'DataSpec': data_spec,
            'RoleARN': role_arn,
        }
        if data_source_name is not None:
            params['DataSourceName'] = data_source_name
        if compute_statistics is not None:
            params['ComputeStatistics'] = compute_statistics
        return self.make_request(action='CreateDataSourceFromRedshift',
                                 body=json.dumps(params))

    def create_data_source_from_s3(self, data_source_id, data_spec,
                                   data_source_name=None,
                                   compute_statistics=None):
        """
        Creates a `DataSource` object. A `DataSource` references data
        that can be used to perform CreateMLModel, CreateEvaluation,
        or CreateBatchPrediction operations.

        `CreateDataSourceFromS3` is an asynchronous operation. In
        response to `CreateDataSourceFromS3`, Amazon Machine Learning
        (Amazon ML) immediately returns and sets the `DataSource`
        status to `PENDING`. After the `DataSource` is created and
        ready for use, Amazon ML sets the `Status` parameter to
        `COMPLETED`. `DataSource` in `COMPLETED` or `PENDING` status
        can only be used to perform CreateMLModel, CreateEvaluation or
        CreateBatchPrediction operations.

        If Amazon ML cannot accept the input source, it sets the
        `Status` parameter to `FAILED` and includes an error message
        in the `Message` attribute of the GetDataSource operation
        response.

        The observation data used in a `DataSource` should be ready to
        use; that is, it should have a consistent structure, and
        missing data values should be kept to a minimum. The
        observation data must reside in one or more CSV files in an
        Amazon Simple Storage Service (Amazon S3) bucket, along with a
        schema that describes the data items by name and type. The
        same schema must be used for all of the data files referenced
        by the `DataSource`.

        After the `DataSource` has been created, it's ready to use in
        evaluations and batch predictions. If you plan to use the
        `DataSource` to train an `MLModel`, the `DataSource` requires
        another item: a recipe. A recipe describes the observation
        variables that participate in training an `MLModel`. A recipe
        describes how each input variable will be used in training.
        Will the variable be included or excluded from training? Will
        the variable be manipulated, for example, combined with
        another variable, or split apart into word combinations? The
        recipe provides answers to these questions. For more
        information, see the `Amazon Machine Learning Developer
        Guide`_.

        :type data_source_id: string
        :param data_source_id: A user-supplied identifier that uniquely
            identifies the `DataSource`.

        :type data_source_name: string
        :param data_source_name: A user-supplied name or description of the
            `DataSource`.

        :type data_spec: dict
        :param data_spec:
        The data specification of a `DataSource`:


        + DataLocationS3 - Amazon Simple Storage Service (Amazon S3) location
              of the observation data.
        + DataSchemaLocationS3 - Amazon S3 location of the `DataSchema`.
        + DataSchema - A JSON string representing the schema. This is not
              required if `DataSchemaUri` is specified.
        + DataRearrangement - A JSON string representing the splitting
              requirement of a `Datasource`. Sample - ` "{\"randomSeed\":\"some-
              random-seed\",
              \"splitting\":{\"percentBegin\":10,\"percentEnd\":60}}"`

        :type compute_statistics: boolean
        :param compute_statistics: The compute statistics for a `DataSource`.
            The statistics are generated from the observation data referenced
            by a `DataSource`. Amazon ML uses the statistics internally during
            an `MLModel` training. This parameter must be set to `True` if the
            ``DataSource `` needs to be used for `MLModel` training

        """
        params = {
            'DataSourceId': data_source_id,
            'DataSpec': data_spec,
        }
        if data_source_name is not None:
            params['DataSourceName'] = data_source_name
        if compute_statistics is not None:
            params['ComputeStatistics'] = compute_statistics
        return self.make_request(action='CreateDataSourceFromS3',
                                 body=json.dumps(params))

    def create_evaluation(self, evaluation_id, ml_model_id,
                          evaluation_data_source_id, evaluation_name=None):
        """
        Creates a new `Evaluation` of an `MLModel`. An `MLModel` is
        evaluated on a set of observations associated to a
        `DataSource`. Like a `DataSource` for an `MLModel`, the
        `DataSource` for an `Evaluation` contains values for the
        Target Variable. The `Evaluation` compares the predicted
        result for each observation to the actual outcome and provides
        a summary so that you know how effective the `MLModel`
        functions on the test data. Evaluation generates a relevant
        performance metric such as BinaryAUC, RegressionRMSE or
        MulticlassAvgFScore based on the corresponding `MLModelType`:
        `BINARY`, `REGRESSION` or `MULTICLASS`.

        `CreateEvaluation` is an asynchronous operation. In response
        to `CreateEvaluation`, Amazon Machine Learning (Amazon ML)
        immediately returns and sets the evaluation status to
        `PENDING`. After the `Evaluation` is created and ready for
        use, Amazon ML sets the status to `COMPLETED`.

        You can use the GetEvaluation operation to check progress of
        the evaluation during the creation operation.

        :type evaluation_id: string
        :param evaluation_id: A user-supplied ID that uniquely identifies the
            `Evaluation`.

        :type evaluation_name: string
        :param evaluation_name: A user-supplied name or description of the
            `Evaluation`.

        :type ml_model_id: string
        :param ml_model_id: The ID of the `MLModel` to evaluate.
        The schema used in creating the `MLModel` must match the schema of the
            `DataSource` used in the `Evaluation`.

        :type evaluation_data_source_id: string
        :param evaluation_data_source_id: The ID of the `DataSource` for the
            evaluation. The schema of the `DataSource` must match the schema
            used to create the `MLModel`.

        """
        params = {
            'EvaluationId': evaluation_id,
            'MLModelId': ml_model_id,
            'EvaluationDataSourceId': evaluation_data_source_id,
        }
        if evaluation_name is not None:
            params['EvaluationName'] = evaluation_name
        return self.make_request(action='CreateEvaluation',
                                 body=json.dumps(params))

    def create_ml_model(self, ml_model_id, ml_model_type,
                        training_data_source_id, ml_model_name=None,
                        parameters=None, recipe=None, recipe_uri=None):
        """
        Creates a new `MLModel` using the data files and the recipe as
        information sources.

        An `MLModel` is nearly immutable. Users can only update the
        `MLModelName` and the `ScoreThreshold` in an `MLModel` without
        creating a new `MLModel`.

        `CreateMLModel` is an asynchronous operation. In response to
        `CreateMLModel`, Amazon Machine Learning (Amazon ML)
        immediately returns and sets the `MLModel` status to
        `PENDING`. After the `MLModel` is created and ready for use,
        Amazon ML sets the status to `COMPLETED`.

        You can use the GetMLModel operation to check progress of the
        `MLModel` during the creation operation.

        CreateMLModel requires a `DataSource` with computed
        statistics, which can be created by setting
        `ComputeStatistics` to `True` in CreateDataSourceFromRDS,
        CreateDataSourceFromS3, or CreateDataSourceFromRedshift
        operations.

        :type ml_model_id: string
        :param ml_model_id: A user-supplied ID that uniquely identifies the
            `MLModel`.

        :type ml_model_name: string
        :param ml_model_name: A user-supplied name or description of the
            `MLModel`.

        :type ml_model_type: string
        :param ml_model_type: The category of supervised learning that this
            `MLModel` will address. Choose from the following types:

        + Choose `REGRESSION` if the `MLModel` will be used to predict a
              numeric value.
        + Choose `BINARY` if the `MLModel` result has two possible values.
        + Choose `MULTICLASS` if the `MLModel` result has a limited number of
              values.


        For more information, see the `Amazon Machine Learning Developer
            Guide`_.

        :type parameters: map
        :param parameters:
        A list of the training parameters in the `MLModel`. The list is
            implemented as a map of key/value pairs.

        The following is the current set of training parameters:


        + `sgd.l1RegularizationAmount` - Coefficient regularization L1 norm. It
              controls overfitting the data by penalizing large coefficients.
              This tends to drive coefficients to zero, resulting in sparse
              feature set. If you use this parameter, start by specifying a small
              value such as 1.0E-08. The value is a double that ranges from 0 to
              MAX_DOUBLE. The default is not to use L1 normalization. The
              parameter cannot be used when `L2` is specified. Use this parameter
              sparingly.
        + `sgd.l2RegularizationAmount` - Coefficient regularization L2 norm. It
              controls overfitting the data by penalizing large coefficients.
              This tends to drive coefficients to small, nonzero values. If you
              use this parameter, start by specifying a small value such as
              1.0E-08. The valuseis a double that ranges from 0 to MAX_DOUBLE.
              The default is not to use L2 normalization. This cannot be used
              when `L1` is specified. Use this parameter sparingly.
        + `sgd.maxPasses` - Number of times that the training process traverses
              the observations to build the `MLModel`. The value is an integer
              that ranges from 1 to 10000. The default value is 10.
        + `sgd.maxMLModelSizeInBytes` - Maximum allowed size of the model.
              Depending on the input data, the size of the model might affect its
              performance. The value is an integer that ranges from 100000 to
              2147483648. The default value is 33554432.

        :type training_data_source_id: string
        :param training_data_source_id: The `DataSource` that points to the
            training data.

        :type recipe: string
        :param recipe: The data recipe for creating `MLModel`. You must specify
            either the recipe or its URI. If you dont specify a recipe or its
            URI, Amazon ML creates a default.

        :type recipe_uri: string
        :param recipe_uri: The Amazon Simple Storage Service (Amazon S3)
            location and file name that contains the `MLModel` recipe. You must
            specify either the recipe or its URI. If you dont specify a recipe
            or its URI, Amazon ML creates a default.

        """
        params = {
            'MLModelId': ml_model_id,
            'MLModelType': ml_model_type,
            'TrainingDataSourceId': training_data_source_id,
        }
        if ml_model_name is not None:
            params['MLModelName'] = ml_model_name
        if parameters is not None:
            params['Parameters'] = parameters
        if recipe is not None:
            params['Recipe'] = recipe
        if recipe_uri is not None:
            params['RecipeUri'] = recipe_uri
        return self.make_request(action='CreateMLModel',
                                 body=json.dumps(params))

    def create_realtime_endpoint(self, ml_model_id):
        """
        Creates a real-time endpoint for the `MLModel`. The endpoint
        contains the URI of the `MLModel`; that is, the location to
        send real-time prediction requests for the specified
        `MLModel`.

        :type ml_model_id: string
        :param ml_model_id: The ID assigned to the `MLModel` during creation.

        """
        params = {'MLModelId': ml_model_id, }
        return self.make_request(action='CreateRealtimeEndpoint',
                                 body=json.dumps(params))

    def delete_batch_prediction(self, batch_prediction_id):
        """
        Assigns the DELETED status to a `BatchPrediction`, rendering
        it unusable.

        After using the `DeleteBatchPrediction` operation, you can use
        the GetBatchPrediction operation to verify that the status of
        the `BatchPrediction` changed to DELETED.

        The result of the `DeleteBatchPrediction` operation is
        irreversible.

        :type batch_prediction_id: string
        :param batch_prediction_id: A user-supplied ID that uniquely identifies
            the `BatchPrediction`.

        """
        params = {'BatchPredictionId': batch_prediction_id, }
        return self.make_request(action='DeleteBatchPrediction',
                                 body=json.dumps(params))

    def delete_data_source(self, data_source_id):
        """
        Assigns the DELETED status to a `DataSource`, rendering it
        unusable.

        After using the `DeleteDataSource` operation, you can use the
        GetDataSource operation to verify that the status of the
        `DataSource` changed to DELETED.

        The results of the `DeleteDataSource` operation are
        irreversible.

        :type data_source_id: string
        :param data_source_id: A user-supplied ID that uniquely identifies the
            `DataSource`.

        """
        params = {'DataSourceId': data_source_id, }
        return self.make_request(action='DeleteDataSource',
                                 body=json.dumps(params))

    def delete_evaluation(self, evaluation_id):
        """
        Assigns the `DELETED` status to an `Evaluation`, rendering it
        unusable.

        After invoking the `DeleteEvaluation` operation, you can use
        the GetEvaluation operation to verify that the status of the
        `Evaluation` changed to `DELETED`.

        The results of the `DeleteEvaluation` operation are
        irreversible.

        :type evaluation_id: string
        :param evaluation_id: A user-supplied ID that uniquely identifies the
            `Evaluation` to delete.

        """
        params = {'EvaluationId': evaluation_id, }
        return self.make_request(action='DeleteEvaluation',
                                 body=json.dumps(params))

    def delete_ml_model(self, ml_model_id):
        """
        Assigns the DELETED status to an `MLModel`, rendering it
        unusable.

        After using the `DeleteMLModel` operation, you can use the
        GetMLModel operation to verify that the status of the
        `MLModel` changed to DELETED.

        The result of the `DeleteMLModel` operation is irreversible.

        :type ml_model_id: string
        :param ml_model_id: A user-supplied ID that uniquely identifies the
            `MLModel`.

        """
        params = {'MLModelId': ml_model_id, }
        return self.make_request(action='DeleteMLModel',
                                 body=json.dumps(params))

    def delete_realtime_endpoint(self, ml_model_id):
        """
        Deletes a real time endpoint of an `MLModel`.

        :type ml_model_id: string
        :param ml_model_id: The ID assigned to the `MLModel` during creation.

        """
        params = {'MLModelId': ml_model_id, }
        return self.make_request(action='DeleteRealtimeEndpoint',
                                 body=json.dumps(params))

    def describe_batch_predictions(self, filter_variable=None, eq=None,
                                   gt=None, lt=None, ge=None, le=None,
                                   ne=None, prefix=None, sort_order=None,
                                   next_token=None, limit=None):
        """
        Returns a list of `BatchPrediction` operations that match the
        search criteria in the request.

        :type filter_variable: string
        :param filter_variable:
        Use one of the following variables to filter a list of
            `BatchPrediction`:


        + `CreatedAt` - Sets the search criteria to the `BatchPrediction`
              creation date.
        + `Status` - Sets the search criteria to the `BatchPrediction` status.
        + `Name` - Sets the search criteria to the contents of the
              `BatchPrediction` ** ** `Name`.
        + `IAMUser` - Sets the search criteria to the user account that invoked
              the `BatchPrediction` creation.
        + `MLModelId` - Sets the search criteria to the `MLModel` used in the
              `BatchPrediction`.
        + `DataSourceId` - Sets the search criteria to the `DataSource` used in
              the `BatchPrediction`.
        + `DataURI` - Sets the search criteria to the data file(s) used in the
              `BatchPrediction`. The URL can identify either a file or an Amazon
              Simple Storage Solution (Amazon S3) bucket or directory.

        :type eq: string
        :param eq: The equal to operator. The `BatchPrediction` results will
            have `FilterVariable` values that exactly match the value specified
            with `EQ`.

        :type gt: string
        :param gt: The greater than operator. The `BatchPrediction` results
            will have `FilterVariable` values that are greater than the value
            specified with `GT`.

        :type lt: string
        :param lt: The less than operator. The `BatchPrediction` results will
            have `FilterVariable` values that are less than the value specified
            with `LT`.

        :type ge: string
        :param ge: The greater than or equal to operator. The `BatchPrediction`
            results will have `FilterVariable` values that are greater than or
            equal to the value specified with `GE`.

        :type le: string
        :param le: The less than or equal to operator. The `BatchPrediction`
            results will have `FilterVariable` values that are less than or
            equal to the value specified with `LE`.

        :type ne: string
        :param ne: The not equal to operator. The `BatchPrediction` results
            will have `FilterVariable` values not equal to the value specified
            with `NE`.

        :type prefix: string
        :param prefix:
        A string that is found at the beginning of a variable, such as `Name`
            or `Id`.

        For example, a `Batch Prediction` operation could have the `Name`
            `2014-09-09-HolidayGiftMailer`. To search for this
            `BatchPrediction`, select `Name` for the `FilterVariable` and any
            of the following strings for the `Prefix`:


        + 2014-09
        + 2014-09-09
        + 2014-09-09-Holiday

        :type sort_order: string
        :param sort_order: A two-value parameter that determines the sequence
            of the resulting list of `MLModel`s.

        + `asc` - Arranges the list in ascending order (A-Z, 0-9).
        + `dsc` - Arranges the list in descending order (Z-A, 9-0).


        Results are sorted by `FilterVariable`.

        :type next_token: string
        :param next_token: An ID of the page in the paginated results.

        :type limit: integer
        :param limit: The number of pages of information to include in the
            result. The range of acceptable values is 1 through 100. The
            default value is 100.

        """
        params = {}
        if filter_variable is not None:
            params['FilterVariable'] = filter_variable
        if eq is not None:
            params['EQ'] = eq
        if gt is not None:
            params['GT'] = gt
        if lt is not None:
            params['LT'] = lt
        if ge is not None:
            params['GE'] = ge
        if le is not None:
            params['LE'] = le
        if ne is not None:
            params['NE'] = ne
        if prefix is not None:
            params['Prefix'] = prefix
        if sort_order is not None:
            params['SortOrder'] = sort_order
        if next_token is not None:
            params['NextToken'] = next_token
        if limit is not None:
            params['Limit'] = limit
        return self.make_request(action='DescribeBatchPredictions',
                                 body=json.dumps(params))

    def describe_data_sources(self, filter_variable=None, eq=None, gt=None,
                              lt=None, ge=None, le=None, ne=None,
                              prefix=None, sort_order=None, next_token=None,
                              limit=None):
        """
        Returns a list of `DataSource` that match the search criteria
        in the request.

        :type filter_variable: string
        :param filter_variable:
        Use one of the following variables to filter a list of `DataSource`:


        + `CreatedAt` - Sets the search criteria to `DataSource` creation
              dates.
        + `Status` - Sets the search criteria to `DataSource` statuses.
        + `Name` - Sets the search criteria to the contents of `DataSource` **
              ** `Name`.
        + `DataUri` - Sets the search criteria to the URI of data files used to
              create the `DataSource`. The URI can identify either a file or an
              Amazon Simple Storage Service (Amazon S3) bucket or directory.
        + `IAMUser` - Sets the search criteria to the user account that invoked
              the `DataSource` creation.

        :type eq: string
        :param eq: The equal to operator. The `DataSource` results will have
            `FilterVariable` values that exactly match the value specified with
            `EQ`.

        :type gt: string
        :param gt: The greater than operator. The `DataSource` results will
            have `FilterVariable` values that are greater than the value
            specified with `GT`.

        :type lt: string
        :param lt: The less than operator. The `DataSource` results will have
            `FilterVariable` values that are less than the value specified with
            `LT`.

        :type ge: string
        :param ge: The greater than or equal to operator. The `DataSource`
            results will have `FilterVariable` values that are greater than or
            equal to the value specified with `GE`.

        :type le: string
        :param le: The less than or equal to operator. The `DataSource` results
            will have `FilterVariable` values that are less than or equal to
            the value specified with `LE`.

        :type ne: string
        :param ne: The not equal to operator. The `DataSource` results will
            have `FilterVariable` values not equal to the value specified with
            `NE`.

        :type prefix: string
        :param prefix:
        A string that is found at the beginning of a variable, such as `Name`
            or `Id`.

        For example, a `DataSource` could have the `Name`
            `2014-09-09-HolidayGiftMailer`. To search for this `DataSource`,
            select `Name` for the `FilterVariable` and any of the following
            strings for the `Prefix`:


        + 2014-09
        + 2014-09-09
        + 2014-09-09-Holiday

        :type sort_order: string
        :param sort_order: A two-value parameter that determines the sequence
            of the resulting list of `DataSource`.

        + `asc` - Arranges the list in ascending order (A-Z, 0-9).
        + `dsc` - Arranges the list in descending order (Z-A, 9-0).


        Results are sorted by `FilterVariable`.

        :type next_token: string
        :param next_token: The ID of the page in the paginated results.

        :type limit: integer
        :param limit: The maximum number of `DataSource` to include in the
            result.

        """
        params = {}
        if filter_variable is not None:
            params['FilterVariable'] = filter_variable
        if eq is not None:
            params['EQ'] = eq
        if gt is not None:
            params['GT'] = gt
        if lt is not None:
            params['LT'] = lt
        if ge is not None:
            params['GE'] = ge
        if le is not None:
            params['LE'] = le
        if ne is not None:
            params['NE'] = ne
        if prefix is not None:
            params['Prefix'] = prefix
        if sort_order is not None:
            params['SortOrder'] = sort_order
        if next_token is not None:
            params['NextToken'] = next_token
        if limit is not None:
            params['Limit'] = limit
        return self.make_request(action='DescribeDataSources',
                                 body=json.dumps(params))

    def describe_evaluations(self, filter_variable=None, eq=None, gt=None,
                             lt=None, ge=None, le=None, ne=None, prefix=None,
                             sort_order=None, next_token=None, limit=None):
        """
        Returns a list of `DescribeEvaluations` that match the search
        criteria in the request.

        :type filter_variable: string
        :param filter_variable:
        Use one of the following variable to filter a list of `Evaluation`
            objects:


        + `CreatedAt` - Sets the search criteria to the `Evaluation` creation
              date.
        + `Status` - Sets the search criteria to the `Evaluation` status.
        + `Name` - Sets the search criteria to the contents of `Evaluation` **
              ** `Name`.
        + `IAMUser` - Sets the search criteria to the user account that invoked
              an `Evaluation`.
        + `MLModelId` - Sets the search criteria to the `MLModel` that was
              evaluated.
        + `DataSourceId` - Sets the search criteria to the `DataSource` used in
              `Evaluation`.
        + `DataUri` - Sets the search criteria to the data file(s) used in
              `Evaluation`. The URL can identify either a file or an Amazon
              Simple Storage Solution (Amazon S3) bucket or directory.

        :type eq: string
        :param eq: The equal to operator. The `Evaluation` results will have
            `FilterVariable` values that exactly match the value specified with
            `EQ`.

        :type gt: string
        :param gt: The greater than operator. The `Evaluation` results will
            have `FilterVariable` values that are greater than the value
            specified with `GT`.

        :type lt: string
        :param lt: The less than operator. The `Evaluation` results will have
            `FilterVariable` values that are less than the value specified with
            `LT`.

        :type ge: string
        :param ge: The greater than or equal to operator. The `Evaluation`
            results will have `FilterVariable` values that are greater than or
            equal to the value specified with `GE`.

        :type le: string
        :param le: The less than or equal to operator. The `Evaluation` results
            will have `FilterVariable` values that are less than or equal to
            the value specified with `LE`.

        :type ne: string
        :param ne: The not equal to operator. The `Evaluation` results will
            have `FilterVariable` values not equal to the value specified with
            `NE`.

        :type prefix: string
        :param prefix:
        A string that is found at the beginning of a variable, such as `Name`
            or `Id`.

        For example, an `Evaluation` could have the `Name`
            `2014-09-09-HolidayGiftMailer`. To search for this `Evaluation`,
            select `Name` for the `FilterVariable` and any of the following
            strings for the `Prefix`:


        + 2014-09
        + 2014-09-09
        + 2014-09-09-Holiday

        :type sort_order: string
        :param sort_order: A two-value parameter that determines the sequence
            of the resulting list of `Evaluation`.

        + `asc` - Arranges the list in ascending order (A-Z, 0-9).
        + `dsc` - Arranges the list in descending order (Z-A, 9-0).


        Results are sorted by `FilterVariable`.

        :type next_token: string
        :param next_token: The ID of the page in the paginated results.

        :type limit: integer
        :param limit: The maximum number of `Evaluation` to include in the
            result.

        """
        params = {}
        if filter_variable is not None:
            params['FilterVariable'] = filter_variable
        if eq is not None:
            params['EQ'] = eq
        if gt is not None:
            params['GT'] = gt
        if lt is not None:
            params['LT'] = lt
        if ge is not None:
            params['GE'] = ge
        if le is not None:
            params['LE'] = le
        if ne is not None:
            params['NE'] = ne
        if prefix is not None:
            params['Prefix'] = prefix
        if sort_order is not None:
            params['SortOrder'] = sort_order
        if next_token is not None:
            params['NextToken'] = next_token
        if limit is not None:
            params['Limit'] = limit
        return self.make_request(action='DescribeEvaluations',
                                 body=json.dumps(params))

    def describe_ml_models(self, filter_variable=None, eq=None, gt=None,
                           lt=None, ge=None, le=None, ne=None, prefix=None,
                           sort_order=None, next_token=None, limit=None):
        """
        Returns a list of `MLModel` that match the search criteria in
        the request.

        :type filter_variable: string
        :param filter_variable:
        Use one of the following variables to filter a list of `MLModel`:


        + `CreatedAt` - Sets the search criteria to `MLModel` creation date.
        + `Status` - Sets the search criteria to `MLModel` status.
        + `Name` - Sets the search criteria to the contents of `MLModel` ** **
              `Name`.
        + `IAMUser` - Sets the search criteria to the user account that invoked
              the `MLModel` creation.
        + `TrainingDataSourceId` - Sets the search criteria to the `DataSource`
              used to train one or more `MLModel`.
        + `RealtimeEndpointStatus` - Sets the search criteria to the `MLModel`
              real-time endpoint status.
        + `MLModelType` - Sets the search criteria to `MLModel` type: binary,
              regression, or multi-class.
        + `Algorithm` - Sets the search criteria to the algorithm that the
              `MLModel` uses.
        + `TrainingDataURI` - Sets the search criteria to the data file(s) used
              in training a `MLModel`. The URL can identify either a file or an
              Amazon Simple Storage Service (Amazon S3) bucket or directory.

        :type eq: string
        :param eq: The equal to operator. The `MLModel` results will have
            `FilterVariable` values that exactly match the value specified with
            `EQ`.

        :type gt: string
        :param gt: The greater than operator. The `MLModel` results will have
            `FilterVariable` values that are greater than the value specified
            with `GT`.

        :type lt: string
        :param lt: The less than operator. The `MLModel` results will have
            `FilterVariable` values that are less than the value specified with
            `LT`.

        :type ge: string
        :param ge: The greater than or equal to operator. The `MLModel` results
            will have `FilterVariable` values that are greater than or equal to
            the value specified with `GE`.

        :type le: string
        :param le: The less than or equal to operator. The `MLModel` results
            will have `FilterVariable` values that are less than or equal to
            the value specified with `LE`.

        :type ne: string
        :param ne: The not equal to operator. The `MLModel` results will have
            `FilterVariable` values not equal to the value specified with `NE`.

        :type prefix: string
        :param prefix:
        A string that is found at the beginning of a variable, such as `Name`
            or `Id`.

        For example, an `MLModel` could have the `Name`
            `2014-09-09-HolidayGiftMailer`. To search for this `MLModel`,
            select `Name` for the `FilterVariable` and any of the following
            strings for the `Prefix`:


        + 2014-09
        + 2014-09-09
        + 2014-09-09-Holiday

        :type sort_order: string
        :param sort_order: A two-value parameter that determines the sequence
            of the resulting list of `MLModel`.

        + `asc` - Arranges the list in ascending order (A-Z, 0-9).
        + `dsc` - Arranges the list in descending order (Z-A, 9-0).


        Results are sorted by `FilterVariable`.

        :type next_token: string
        :param next_token: The ID of the page in the paginated results.

        :type limit: integer
        :param limit: The number of pages of information to include in the
            result. The range of acceptable values is 1 through 100. The
            default value is 100.

        """
        params = {}
        if filter_variable is not None:
            params['FilterVariable'] = filter_variable
        if eq is not None:
            params['EQ'] = eq
        if gt is not None:
            params['GT'] = gt
        if lt is not None:
            params['LT'] = lt
        if ge is not None:
            params['GE'] = ge
        if le is not None:
            params['LE'] = le
        if ne is not None:
            params['NE'] = ne
        if prefix is not None:
            params['Prefix'] = prefix
        if sort_order is not None:
            params['SortOrder'] = sort_order
        if next_token is not None:
            params['NextToken'] = next_token
        if limit is not None:
            params['Limit'] = limit
        return self.make_request(action='DescribeMLModels',
                                 body=json.dumps(params))

    def get_batch_prediction(self, batch_prediction_id):
        """
        Returns a `BatchPrediction` that includes detailed metadata,
        status, and data file information for a `Batch Prediction`
        request.

        :type batch_prediction_id: string
        :param batch_prediction_id: An ID assigned to the `BatchPrediction` at
            creation.

        """
        params = {'BatchPredictionId': batch_prediction_id, }
        return self.make_request(action='GetBatchPrediction',
                                 body=json.dumps(params))

    def get_data_source(self, data_source_id, verbose=None):
        """
        Returns a `DataSource` that includes metadata and data file
        information, as well as the current status of the
        `DataSource`.

        `GetDataSource` provides results in normal or verbose format.
        The verbose format adds the schema description and the list of
        files pointed to by the DataSource to the normal format.

        :type data_source_id: string
        :param data_source_id: The ID assigned to the `DataSource` at creation.

        :type verbose: boolean
        :param verbose: Specifies whether the `GetDataSource` operation should
            return `DataSourceSchema`.
        If true, `DataSourceSchema` is returned.

        If false, `DataSourceSchema` is not returned.

        """
        params = {'DataSourceId': data_source_id, }
        if verbose is not None:
            params['Verbose'] = verbose
        return self.make_request(action='GetDataSource',
                                 body=json.dumps(params))

    def get_evaluation(self, evaluation_id):
        """
        Returns an `Evaluation` that includes metadata as well as the
        current status of the `Evaluation`.

        :type evaluation_id: string
        :param evaluation_id: The ID of the `Evaluation` to retrieve. The
            evaluation of each `MLModel` is recorded and cataloged. The ID
            provides the means to access the information.

        """
        params = {'EvaluationId': evaluation_id, }
        return self.make_request(action='GetEvaluation',
                                 body=json.dumps(params))

    def get_ml_model(self, ml_model_id, verbose=None):
        """
        Returns an `MLModel` that includes detailed metadata, and data
        source information as well as the current status of the
        `MLModel`.

        `GetMLModel` provides results in normal or verbose format.

        :type ml_model_id: string
        :param ml_model_id: The ID assigned to the `MLModel` at creation.

        :type verbose: boolean
        :param verbose: Specifies whether the `GetMLModel` operation should
            return `Recipe`.
        If true, `Recipe` is returned.

        If false, `Recipe` is not returned.

        """
        params = {'MLModelId': ml_model_id, }
        if verbose is not None:
            params['Verbose'] = verbose
        return self.make_request(action='GetMLModel',
                                 body=json.dumps(params))

    def predict(self, ml_model_id, record, predict_endpoint):
        """
        Generates a prediction for the observation using the specified
        `MLModel`.


        Not all response parameters will be populated because this is
        dependent on the type of requested model.

        :type ml_model_id: string
        :param ml_model_id: A unique identifier of the `MLModel`.

        :type record: map
        :param record: A map of variable name-value pairs that represent an
            observation.

        :type predict_endpoint: string
        :param predict_endpoint: The endpoint to send the predict request to.

        """
        predict_host =  urlsplit(predict_endpoint).hostname
        if predict_host is None:
            predict_host = predict_endpoint

        params = {
            'MLModelId': ml_model_id,
            'Record': record,
            'PredictEndpoint': predict_host,
        }
        return self.make_request(action='Predict',
                                 body=json.dumps(params),
                                 host=predict_host)

    def update_batch_prediction(self, batch_prediction_id,
                                batch_prediction_name):
        """
        Updates the `BatchPredictionName` of a `BatchPrediction`.

        You can use the GetBatchPrediction operation to view the
        contents of the updated data element.

        :type batch_prediction_id: string
        :param batch_prediction_id: The ID assigned to the `BatchPrediction`
            during creation.

        :type batch_prediction_name: string
        :param batch_prediction_name: A new user-supplied name or description
            of the `BatchPrediction`.

        """
        params = {
            'BatchPredictionId': batch_prediction_id,
            'BatchPredictionName': batch_prediction_name,
        }
        return self.make_request(action='UpdateBatchPrediction',
                                 body=json.dumps(params))

    def update_data_source(self, data_source_id, data_source_name):
        """
        Updates the `DataSourceName` of a `DataSource`.

        You can use the GetDataSource operation to view the contents
        of the updated data element.

        :type data_source_id: string
        :param data_source_id: The ID assigned to the `DataSource` during
            creation.

        :type data_source_name: string
        :param data_source_name: A new user-supplied name or description of the
            `DataSource` that will replace the current description.

        """
        params = {
            'DataSourceId': data_source_id,
            'DataSourceName': data_source_name,
        }
        return self.make_request(action='UpdateDataSource',
                                 body=json.dumps(params))

    def update_evaluation(self, evaluation_id, evaluation_name):
        """
        Updates the `EvaluationName` of an `Evaluation`.

        You can use the GetEvaluation operation to view the contents
        of the updated data element.

        :type evaluation_id: string
        :param evaluation_id: The ID assigned to the `Evaluation` during
            creation.

        :type evaluation_name: string
        :param evaluation_name: A new user-supplied name or description of the
            `Evaluation` that will replace the current content.

        """
        params = {
            'EvaluationId': evaluation_id,
            'EvaluationName': evaluation_name,
        }
        return self.make_request(action='UpdateEvaluation',
                                 body=json.dumps(params))

    def update_ml_model(self, ml_model_id, ml_model_name=None,
                        score_threshold=None):
        """
        Updates the `MLModelName` and the `ScoreThreshold` of an
        `MLModel`.

        You can use the GetMLModel operation to view the contents of
        the updated data element.

        :type ml_model_id: string
        :param ml_model_id: The ID assigned to the `MLModel` during creation.

        :type ml_model_name: string
        :param ml_model_name: A user-supplied name or description of the
            `MLModel`.

        :type score_threshold: float
        :param score_threshold: The `ScoreThreshold` used in binary
            classification `MLModel` that marks the boundary between a positive
            prediction and a negative prediction.
        Output values greater than or equal to the `ScoreThreshold` receive a
            positive result from the `MLModel`, such as `True`. Output values
            less than the `ScoreThreshold` receive a negative response from the
            `MLModel`, such as `False`.

        """
        params = {'MLModelId': ml_model_id, }
        if ml_model_name is not None:
            params['MLModelName'] = ml_model_name
        if score_threshold is not None:
            params['ScoreThreshold'] = score_threshold
        return self.make_request(action='UpdateMLModel',
                                 body=json.dumps(params))

    def make_request(self, action, body, host=None):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request_kwargs = {
            'method':'POST', 'path':'/', 'auth_path':'/', 'params':{},
            'headers': headers, 'data':body
        }
        if host is not None:
            headers['Host'] = host
            http_request_kwargs['host'] = host
        http_request = self.build_base_http_request(**http_request_kwargs)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

