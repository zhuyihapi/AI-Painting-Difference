# -*- coding: utf-8 -*-

"""
@Time        : 2023/4
@Author      : ZYH
@File        : test_factory
@Description : 
"""
from flaskr import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_index(client):
    response = client.get('/')
    # assert response.data == b'Hello, Index page!'
