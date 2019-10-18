import importlib
import re

import jinja2

from protobuf.proto_grain_generator.proto import ProtoFile, ProtoService, ProtoMethod


class GrainGen:

    def generate(self, path: str) -> str:
        proto_file = self.__get_proto_file(path)
        env = jinja2.Environment(loader=jinja2.PackageLoader('protobuf', 'templates'))
        env.globals['convert_to_snake_case'] = self.__convert_to_snake_case
        template = env.get_template('template.txt')
        return template.render(proto_file=proto_file)

    @staticmethod
    def __get_proto_file(path: str) -> ProtoFile:
        proto_file = ProtoFile()

        spec = importlib.util.spec_from_file_location(path, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for service_name in module.DESCRIPTOR.services_by_name.keys():
            proto_service = ProtoService(service_name)
            service = module.DESCRIPTOR.services_by_name[service_name]
            for index, method in enumerate(service.methods):
                proto_service.methods.append(ProtoMethod(index,
                                                         method.name,
                                                         method.input_type.name,
                                                         method.output_type.name))
            proto_file.services.append(proto_service)
        return proto_file

    @staticmethod
    def __convert_to_snake_case(string: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


GrainGen = GrainGen()
