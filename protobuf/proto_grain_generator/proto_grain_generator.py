import os
import sys

from protobuf.proto_grain_generator import grain_gen
from protobuf.proto_grain_generator.grain_gen import GrainGen


def main(argv):
    try:
        if len(argv) < 1:
            print('You need to specify a path to the proto file to use')
        else:
            input_file_path = get_input_file_path(argv)
            output_file_path = get_output_file_path(argv)
            grain = GrainGen.generate(input_file_path)

            with open(output_file_path, 'w', encoding="utf-8") as writer:
                writer.write(grain)
    except Exception as ex:
        print(str(ex))


def get_input_file_path(argv):
    if os.path.isabs(argv[0]):
        return argv[0]
    else:
        return os.path.join(os.getcwd(), argv[0])


def get_output_file_path(argv):
    if len(argv) == 1:
        if os.path.isabs(argv[0]):
            file = os.path.basename(argv[0])
            file_name, file_extension = os.path.splitext(file)
            file_name = file_name.split("_")[0]
            return os.path.join(os.path.dirname(argv[0]), f'{file_name}.py')
        else:
            file_name, file_extension = os.path.splitext(argv[0])
            file_name = file_name.split("_")[0]
            return os.path.join(os.getcwd(), f'{file_name}.py')
    else:
        if os.path.isabs(argv[1]):
            return argv[1]
        else:
            return os.path.join(os.getcwd(), argv[1])


if __name__ == "__main__":
    main(sys.argv[1:])

