#!/usr/bin/python3
# -*- coding: utf-8 -*-

class IncorrectStateException(Exception):
    def __init__(self, text):
        super(IncorrectStateException, self).__init__(text)