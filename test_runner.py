# Author: Peter Arandorenko
# Date: January 21, 2024

import argparse
import os
import re
import subprocess

class TestRunner:
    def __init__(self, test_directory, output_directory="bin", language="cpp", blacklist=None):
        self.test_directory = os.path.join(test_directory, language)
        print(f"Test path: {self.test_directory}")
        self.output_directory = os.path.join(output_directory, language)
        self.language = language.lower()
        self.blacklist = blacklist or  []
        os.makedirs(self.output_directory, exist_ok=True)
        
    def discover_tests(self):
        test_files = []
        if self.language == "go":
            for root, _, files in os.walk(".", topdown=False):
                for file in files:
                    if file.endswith("_test.go"):
                        test_files.append(os.path.join(root, file))
        elif self.language == "py":
            test_files = [os.path.join(self.test_directory, file) for file in os.listdir(self.test_directory) if re.search(r"test_*", file)]
        elif self.language == "cpp":
            test_files = [file for file in os.listdir(self.test_directory) if file.endswith(f".{self.language}")]
        else:
            print(f"Failed to detect language [{self.language}]. Discover tests failed.")
            exit(1)
        return test_files
        
    def compile_and_run_test(self, test_file):
        test_name = os.path.splitext(test_file)[0]
        output_binary = os.path.join(self.output_directory, test_name)

        self.compile_and_check(test_file, output_binary)
        self.run_and_check(output_binary)

    def compile_and_check(self, test_file, output_binary):
        compile_command = self.get_compile_command(test_file, output_binary)
        print(f"Compile command: {compile_command}")
        
        compile_result = subprocess.run(compile_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(compile_result.stdout)

        if compile_result.returncode != 0:
            # Compilation failed
            print(f"Compilation failed for {test_file}")
            print(compile_result.stderr)
            exit(1)  # Exit with a non-zero status code

    def run_and_check(self, output_binary):
        run_command = self.get_run_command(output_binary)
        if run_command == "":
            return
        
        run_result = subprocess.run(run_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(run_result.stdout)

        if run_result.returncode != 0:
            # Run failed
            print(f"Run failed for {output_binary}")
            print(run_result.stderr)
            exit(1)  # Exit with a non-zero status code

    def get_compile_command(self, test_file, output_binary):
        # Customize compile commands for different languages
        if self.language == "cpp":
            return f"g++ -fdiagnostics-color=always -g -std=c++17 {os.path.join(self.test_directory, test_file)} -o {output_binary} -lgtest -lgtest_main -pthread -I cget/include/ -L cget/lib/**"
        elif self.language == "go":
            return f"go test -v {test_file}"
        elif self.language == "py":
            return f"pytest-3 -v {test_file}"
        # Add more languages as needed
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def get_run_command(self, output_binary):
        # Customize run commands for different languages
        if self.language == "cpp":
            return output_binary
        elif self.language == "go":
            # Go tests do not produce standalone binaries, 'go build' does. Main application runs 'go build'. 
            return ""
        elif self.language == "py":
            # Python tests do not produce standalone binaries. Main application runs 'python3 <file>'. 
            return ""
        # Add more languages as needed
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def extract_filename_from_path(file_path):
        # Extract the rightmost part until the first forward slash
        return file_path.rsplit('/', 1)[-1]

    def run_tests(self):
        tests = self.discover_tests()

        for test_file in tests:
            if TestRunner.extract_filename_from_path(test_file) in self.blacklist:
                print(f"Skipping test (blacklisted): {test_file}")
                continue

            print(f"")
            print(f"Running test: {test_file}")

            self.compile_and_run_test(test_file)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run tests with blacklist.')
    parser.add_argument('--language', choices=['cpp', 'go', 'py', 'all'], required=True, help='Programming language to run tests on')
    parser.add_argument('--test-directory', default='tests', help='Directory containing the tests')
    parser.add_argument('--blacklist', nargs='+', help='List of files to blacklist')

    args = parser.parse_args()

    if args.language == 'all':
        languages = ['cpp', 'go', 'py']
    else:
        languages = [args.language]

    for language in languages:
        blacklist = args.blacklist if args.blacklist else []
        print(language)
        test_runner = TestRunner(test_directory=args.test_directory, language=language, blacklist=blacklist)
        test_runner.run_tests()