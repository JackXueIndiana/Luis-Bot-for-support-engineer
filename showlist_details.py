# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class ShowListDetails:
    def __init__(
        self,
        alist: str = None,
        guid: str = None,
        age: str = None,
        incidentid: str = None,
        unsupported_list=None,
    ):
        if unsupported_list is None:
            unsupported_list = []
        self.alist = alist
        self.guid = guid
        self.age = age
        self.incidentid = incidentid
        self.unsupported_list = unsupported_list
