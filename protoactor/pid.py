# class PID:
#     def __init__(self, address: str, id: str, ref: 'AbstractProcess') -> None:
#         self.__address = address
#         self.__id = id
#         self.__process = ref
#
#     @property
#     def address(self) -> str:
#         return self.__address
#
#     @property
#     def id(self) -> str:
#         return self.__id
#
#     @property
#     def process(self) -> 'AbstractProcess':
#         return self.__process
#
#     @process.setter
#     def process(self, ref: 'AbstractProcess') -> None:
#         self.__process = ref
#
#     def __repr__(self):
#         return "{} / {}".format(self.__address, self.__id)
#
#     def tell(self, message):
#         self.__process.send_user_message(self, message)
#
#     def send_system_message(self, message):
#         self.__process.send_system_message(self, message)
#
#     def stop(self):
#         self.__process.stop()
