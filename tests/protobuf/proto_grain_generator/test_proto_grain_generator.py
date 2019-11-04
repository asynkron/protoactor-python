import os
import subprocess
import time


# def test_generate_grain_from_template_with_full_path_for_imput_and_output_files():
#     grain_generator_path = os.path.abspath(
#         "../../../protobuf/proto_grain_generator/proto_grain_generator.py")
#
#     file_path = os.path.abspath("./messages/protos.py")
#     if os.path.exists(file_path):
#         os.remove(file_path)
#
#     input_file_path = os.path.abspath("./messages/protos_pb2.py")
#     output_file_path = os.path.abspath("./messages/protos.py")
#
#     process = subprocess.Popen(['python', grain_generator_path, input_file_path, output_file_path],
#                      stdout=subprocess.PIPE,
#                      stdin=subprocess.PIPE)
#
#     time.sleep(1)
#     process.kill()
#
#     assert os.path.exists(file_path)
#
#
# def test_generate_grain_from_template_with_path_to_imput_files():
#     grain_generator_path = os.path.abspath(
#         "../../../protobuf/proto_grain_generator/proto_grain_generator.py")
#
#     file_path = os.path.abspath("./messages/protos.py")
#     if os.path.exists(file_path):
#         os.remove(file_path)
#
#     input_file_path = os.path.abspath("./messages/protos_pb2.py")
#
#     process = subprocess.Popen(['python', grain_generator_path, input_file_path],
#                                stdout=subprocess.PIPE,
#                                stdin=subprocess.PIPE)
#
#     time.sleep(1)
#     process.kill()
#
#     assert os.path.exists(file_path)
#
#
# def test_generate_grain_from_template_with_short_path_for_imput_and_output_files():
#     grain_generator_path = os.path.abspath(
#         "../../../protobuf/proto_grain_generator/proto_grain_generator.py")
#
#     file_path = os.path.abspath("./messages/protos.py")
#     if os.path.exists(file_path):
#         os.remove(file_path)
#
#     input_file_path = "./messages/protos_pb2.py"
#     output_file_path = "./messages/protos.py"
#
#     process = subprocess.Popen(['python', grain_generator_path, input_file_path, output_file_path],
#                      stdout=subprocess.PIPE,
#                      stdin=subprocess.PIPE)
#
#     time.sleep(1)
#     process.kill()
#
#     assert os.path.exists(file_path)

# def test_1():
#     grain_generator_path = os.path.abspath(
#         "../../../protobuf/proto_grain_generator/proto_grain_generator.py")
#
#     input_file_path = os.path.abspath("../../../examples/cluster_grain_hello_world/messages/protos_pb2.py")
#
#     process = subprocess.Popen(['python', grain_generator_path, input_file_path],
#                      stdout=subprocess.PIPE,
#                      stdin=subprocess.PIPE)
#
#     time.sleep(1)
#     process.kill()
#
#     assert True