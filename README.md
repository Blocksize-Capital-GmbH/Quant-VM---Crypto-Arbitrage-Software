# Quant-VM---Crypto-Arbitrage-Software
Quant VM - Software for arbitrage trading - best execution for crypto assets

## Introduction
Arbitrage is one of the oldest methods of trading known for mankind for hundreds of years. Electronic trading made it popular among nonprofessional traders.  

The project contains sources and deployment file for the arbitrage algorithm executed through Quant SDK developed and operated by Blocksize Capital GmbH. 
Trading of the assets is performed through Quant SDK developed by Blocksize Capital GmbH and the user must have an account to access Blocksize Capital trading infrastructure.  

## Installation

Definition of containers is contained in docker-compose.yaml and operated by [docker-compose](https://docs.docker.com/compose/).

Algorithm is deployed like a set of [docker](https://www.docker.com/) containers. The set includes two service containers and the containers of the algorithm:
 * Container with Postgres database
 * Prometheus server
 * Trading algorithm
 * Measurement of response times
 * Measurement of algorithmic performance
 * Portfolio tracker
 * Updater of the open orders

### Postgres database
For database image can be used standard Postgres image thar contains version >=13. The engine should expose port 5432 and the image have to be downloaded to be operational by docker-compose. 
To check whether the image is in the system, please, use `docker images`.

### Prometheus 
Docker image for Prometheus server is created using command executed from project root `cd prometheus; docker build .; cd ..`. 
The base image is *prom/prometheus* that is downloaded automatically. THe Prometheus configuration is located in **prometheus/prometheus.yml**. 
Finally, for correct operation the image exposes port 9090.

### Arbitrage algorithm and supplementary services
Arbitrage algorithm and supplementary services use image that can be created from *Dockerfile* contained in the project with base image *python:3.9-slim-buster* with Python 3.9.
`docker build .` in the root of the project.

Each container can be started using appropriate name using `docker-compose start [name-of-service]`. 
Actually running service are obtained using `docker-compose ps`. 

## Database structure
Services relay on structure of the database schema. 
The structure is described using DDL in file DB_DDL.sql. Executing the file it creates new scheme. It has to be populated prior to the first used of the arbitrage algorithm, namely information about exchanges, currency pairs and currency pair associations to the exchanges. The data are used by arbitrage algorithm to correctly perform trading. 

Running service then automatically populate appropriate tables associated to them. 
In case of any error in the system, it is recorded to *SYSTEM_LOG* table.

## Operation of the algorithm
The algorithm runs based on the configuration provided by database. It can operate simultaneously more than 2 exchanges and more than one currency pair traded at least 2 exchanges.

Supplementary services provided information about latency to the Blocksize Capital server, measurement of algorithm performance, tracking of the portfolio and finally, finalization of the open orders. These services are optional, but they are useful for tracking of problems.

Application was tested on Python 3.9 but there should be no problem to run it on Python 3.8. 
On the other hand, problems with (yet) unsupported packages were detected for Python 3.10 and 3.11. 
Unless the packages are not fixed more recent versions of Python are not available.

### Python virtual environment
To prevent interaction with system Python packages we use virtual environment that is operated by [poetry](https://python-poetry.org/) that simplifies work with virtual environment. 
Actual configuration of the virtual environment is found **pyproject.toml**. During docker image build the virtual environment is installed on the docker image.

## Known issues
The code was not properly tested and so it may contain bugs. Secondly, validation of the algorithm was not executed.
