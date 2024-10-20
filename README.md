# Distributed Brute Force MD5 Hash Cracker

This project implements a distributed brute force MD5 hash cracker. A server assigns each client a range of strings to check for a matching MD5 hash. The client computes the hash for each string in the assigned range and notifies the server if a match is found.

## Features

- **Distributed architecture**: A central server coordinates multiple clients, distributing the workload to ensure efficient brute force operations.
- **MD5 hashing**: Each client computes the MD5 hash for a given range of strings.
- **Server-client communication**: The clients send results back to the server once the correct hash is found.

## Project Components

1. **Server**: Manages the clients, assigns work ranges, and collects results.
2. **Client**: Receives a string range from the server, computes the MD5 hash for each string in the range, and reports the results back to the server.
3. **Protocol Explanation**: Detailed protocol explanation can be found [here](https://docs.google.com/document/d/1CRXPOpVy9bsPZ444wu-YqREei0ZluE77BxzLRqVxF4Y/edit?usp=sharing).
