#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import sys
import time

from six.moves import configparser

from datahub import DataHub
from datahub.exceptions import ResourceExistException, InvalidParameterException, InvalidOperationException
from datahub.models import RecordType, RecordSchema, FieldType, SubscriptionState

current_path = os.path.split(os.path.realpath(__file__))[0]
root_path = os.path.join(current_path, '../..')

configer = configparser.ConfigParser()
configer.read(os.path.join(current_path, '../datahub.ini'))
access_id = configer.get('datahub', 'access_id')
access_key = configer.get('datahub', 'access_key')
endpoint = configer.get('datahub', 'endpoint')

print("=======================================")
print("access_id: %s" % access_id)
print("access_key: %s" % access_key)
print("endpoint: %s" % endpoint)
print("=======================================\n\n")

if not access_id or not access_key or not endpoint:
    print("[access_id, access_key, endpoint] must be set in datahub.ini!")
    sys.exit(-1)

dh = DataHub(access_id, access_key, endpoint)


def clean_topic(datahub_client, project_name, force=False):
    topic_names = datahub_client.list_topic(project_name).topic_names
    for topic_name in topic_names:
        if force:
            clean_subscription(datahub_client, project_name, topic_name)
        datahub_client.delete_topic(project_name, topic_name)


def clean_project(datahub_client, force=False):
    project_names = datahub_client.list_project().project_names
    for project_name in project_names:
        if force:
            clean_topic(datahub_client, project_name)
        try:
            datahub_client.delete_project(project_name)
        except InvalidOperationException:
            pass


def clean_subscription(datahub_client, project_name, topic_name):
    subscriptions = datahub_client.list_subscription(project_name, topic_name, '', 1, 100).subscriptions
    for subscription in subscriptions:
        datahub_client.delete_subscription(project_name, topic_name, subscription.sub_id)


class TestSubscription:

    def test_create_and_delete_subscription(self):
        project_name = "topic_test_p%d_0" % int(time.time())
        topic_name = "topic_test_t%d_0" % int(time.time())

        shard_count = 3
        life_cycle = 7
        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'event_time1'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_tuple_topic(project_name, topic_name, shard_count, life_cycle, record_schema, '')
            except ResourceExistException:
                pass

            # ======================= create subscription =======================
            result = dh.create_subscription(project_name, topic_name, 'comment')
            print(result)
            assert result.sub_id

            # ======================= delete subscription =======================
            dh.delete_subscription(project_name, topic_name, result.sub_id)
        finally:
            clean_topic(dh, project_name, True)
            dh.delete_project(project_name)

    def test_get_subscription(self):
        project_name = "topic_test_p%d_1" % int(time.time())
        topic_name = "topic_test_t%d_1" % int(time.time())

        shard_count = 3
        life_cycle = 7
        
        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'event_time1'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_tuple_topic(project_name, topic_name, shard_count, life_cycle, record_schema, '')
            except ResourceExistException:
                pass

            create_result = dh.create_subscription(project_name, topic_name, 'comment')

            # ======================= get subscription =======================
            result = dh.get_subscription(project_name, topic_name, create_result.sub_id)
            print(result)
            assert result.comment == 'comment'
            assert result.create_time > 0
            assert result.is_owner is True
            assert result.last_modify_time > 0
            assert result.state == SubscriptionState.ACTIVE
            assert result.sub_id == create_result.sub_id
            assert result.topic_name == topic_name
            assert result.type == 0

            dh.delete_subscription(project_name, topic_name, create_result.sub_id)
        finally:
            clean_topic(dh, project_name, True)
            dh.delete_project(project_name)

    def test_update_subscription(self):
        project_name = "topic_test_p%d_2" % int(time.time())
        topic_name = "topic_test_t%d_2" % int(time.time())

        shard_count = 3
        life_cycle = 7
        record_type = RecordType.TUPLE
        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'event_time1'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_tuple_topic(project_name, topic_name, shard_count, life_cycle, record_schema, '')
            except ResourceExistException:
                pass

            create_result = dh.create_subscription(project_name, topic_name, 'comment')
            print(create_result)
            assert create_result.sub_id

            # ======================= update subscription =======================
            dh.update_subscription(project_name, topic_name, create_result.sub_id, 'new comment')
            result = dh.get_subscription(project_name, topic_name, create_result.sub_id)
            print(result)
            assert result.comment == 'new comment'

            dh.delete_subscription(project_name, topic_name, create_result.sub_id)
        finally:
            clean_topic(dh, project_name, True)
            dh.delete_project(project_name)

    def test_update_subscription_state(self):
        project_name = "topic_test_p%d_3" % int(time.time())
        topic_name = "topic_test_t%d_3" % int(time.time())

        shard_count = 3
        life_cycle = 7
        record_type = RecordType.TUPLE
        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'event_time1'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_tuple_topic(project_name, topic_name, shard_count, life_cycle, record_schema, '')
            except ResourceExistException:
                pass

            create_result = dh.create_subscription(project_name, topic_name, 'comment')
            assert create_result.sub_id

            # ======================= update subscription state =======================
            dh.update_subscription_state(project_name, topic_name, create_result.sub_id,
                                         SubscriptionState.INACTIVE)
            result = dh.get_subscription(project_name, topic_name, create_result.sub_id)
            assert result.state == SubscriptionState.INACTIVE
            dh.update_subscription_state(project_name, topic_name, create_result.sub_id,
                                         SubscriptionState.ACTIVE)
            result = dh.get_subscription(project_name, topic_name, create_result.sub_id)
            assert result.state == SubscriptionState.ACTIVE

            dh.delete_subscription(project_name, topic_name, create_result.sub_id)
        finally:
            clean_topic(dh, project_name, True)
            dh.delete_project(project_name)

    def test_list_subscription(self):
        project_name = "topic_test_p%d_4" % int(time.time())
        topic_name = "topic_test_t%d_4" % int(time.time())

        shard_count = 3
        life_cycle = 7
        record_type = RecordType.TUPLE
        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'event_time1'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_tuple_topic(project_name, topic_name, shard_count, life_cycle, record_schema, '')
            except ResourceExistException:
                pass

            create_result = dh.create_subscription(project_name, topic_name, 'comment')
            assert create_result.sub_id

            # ======================= query subscription state =======================
            result = dh.list_subscription(project_name, topic_name, '', 1, 10)
            print(result)

            assert result.total_count == 1
            subscription = result.subscriptions[0]
            assert subscription.comment == 'comment'
            assert subscription.create_time > 0
            assert subscription.is_owner is True
            assert subscription.last_modify_time > 0
            assert subscription.state == SubscriptionState.ACTIVE
            assert subscription.sub_id == create_result.sub_id
            assert subscription.topic_name == topic_name
            assert subscription.type == 0

            try:
                dh.list_subscription(project_name, topic_name, '', 0, 1)
            except InvalidParameterException:
                pass
            else:
                raise Exception('query subscription success with invalid page index')

            try:
                dh.list_subscription(project_name, topic_name, '', 1, -1)
            except InvalidParameterException:
                pass
            else:
                raise Exception('query subscription success with invalid page size')

            dh.delete_subscription(project_name, topic_name, create_result.sub_id)
        finally:
            clean_topic(dh, project_name, True)
            dh.delete_project(project_name)


# run directly
if __name__ == '__main__':
    test = TestSubscription()
    test.test_create_and_delete_subscription()
    test.test_get_subscription()
    test.test_update_subscription()
    test.test_update_subscription_state()
    test.test_list_subscription()
