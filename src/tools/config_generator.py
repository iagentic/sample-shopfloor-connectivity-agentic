#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) Configuration Generator
Provides functions for generating SFC configuration templates
"""

import json
from typing import Dict, Any, List

from src.tools.sfc_knowledge import load_sfc_knowledge


def generate_config_template(
    protocol: str, target: str, environment: str, sfc_knowledge: Dict[str, Any]
) -> str:
    """Generate a configuration template

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
        environment: Environment type (development, production)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        String containing the generated configuration template
    """
    if protocol not in sfc_knowledge["supported_protocols"]:
        return f"❌ Unsupported protocol: {protocol}. Supported: {', '.join(sfc_knowledge['supported_protocols'].keys())}"

    # Create basic template structure
    template = {
        "AWSVersion": sfc_knowledge["aws_version"],
        "Name": f"{protocol} to {target} Configuration",
        "Description": f"{environment.title()} configuration for {protocol} protocol to {target} target",
        "LogLevel": "Info" if environment == "production" else "Trace",
        "Schedules": [
            {
                "Name": f"{protocol}Schedule",
                "Interval": 1000 if environment == "development" else 5000,
                "Active": True,
                "TimestampLevel": "Both",
                "Sources": {f"{protocol}-SOURCE": ["*"]},
                "Targets": [f"{target}Target"],
            }
        ],
        "Sources": generate_source_template(protocol, sfc_knowledge),
        "Targets": generate_target_template(target, environment, sfc_knowledge),
        "TargetTypes": generate_target_types(target, sfc_knowledge),
        "AdapterTypes": generate_adapter_types(protocol, sfc_knowledge),
        "ProtocolAdapters": generate_protocol_adapter_config(protocol, sfc_knowledge),
    }

    return f"✅ Generated {protocol} to {target} template:\n\n```json\n{json.dumps(template, indent=2)}\n```"


def generate_source_template(protocol: str, sfc_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """Generate source configuration template

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing source configuration
    """
    base_config = {
        f"{protocol}-SOURCE": {
            "Name": f"{protocol}Source",
            "ProtocolAdapter": protocol,
            "Description": f"{protocol} source configuration",
            "Channels": {},
        }
    }

    # Add protocol-specific configurations
    if protocol == "OPCUA":
        base_config[f"{protocol}-SOURCE"]["AdapterOpcuaServer"] = "OPCUA-SERVER-1"
        base_config[f"{protocol}-SOURCE"]["SourceReadingMode"] = "Polling"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "ServerStatus": {"NodeId": "ns=0;i=2256"},
            "ServerTime": {"NodeId": "ns=0;i=2256", "Selector": "@.currentTime"},
        }
    elif protocol == "MODBUS":
        base_config[f"{protocol}-SOURCE"]["AdapterDevice"] = "MODBUS-DEVICE-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Register1": {"Address": 40001, "Type": "HoldingRegister"},
            "Register2": {"Address": 40002, "Type": "HoldingRegister"},
        }
    elif protocol == "S7":
        base_config[f"{protocol}-SOURCE"]["AdapterController"] = "S7-PLC-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "DB1Value1": {"Name": "Value1", "Address": "DB100.DBW0", "Type": "Int"},
            "DB1Value2": {"Name": "Value2", "Address": "DB100.DBD4", "Type": "Real"},
        }
    elif protocol == "ADS":
        base_config[f"{protocol}-SOURCE"]["AdapterDevice"] = "ADS-DEVICE-1"
        base_config[f"{protocol}-SOURCE"]["SourceAmsId"] = "192.168.1.10.1.1"
        base_config[f"{protocol}-SOURCE"]["SourceAmsPort"] = 851
        base_config[f"{protocol}-SOURCE"]["TargetAmsId"] = "192.168.1.20.1.1"
        base_config[f"{protocol}-SOURCE"]["TargetAmsPort"] = 852
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Temperature": {"Name": "Temperature", "SymbolName": "MAIN.Temperature"},
            "Pressure": {"Name": "Pressure", "SymbolName": "MAIN.PressureValue"},
        }
    elif protocol == "MQTT":
        base_config[f"{protocol}-SOURCE"]["AdapterBroker"] = "MQTT-BROKER-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Temperature": {"Topics": ["sensors/temperature"]},
            "Humidity": {"Topics": ["sensors/humidity"]},
        }
    elif protocol == "REST":
        base_config[f"{protocol}-SOURCE"]["RestServer"] = "REST-SERVER-1"
        base_config[f"{protocol}-SOURCE"]["Request"] = "/api/sensors"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Temperature": {"Name": "Temperature", "Json": True, "Selector": "@.temperature"},
            "Humidity": {"Name": "Humidity", "Json": True, "Selector": "@.humidity"},
        }
    elif protocol == "SNMP":
        base_config[f"{protocol}-SOURCE"]["AdapterDevice"] = "SNMP-DEVICE-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "SystemUptime": {"Name": "Uptime", "ObjectId": "1.3.6.1.2.1.1.3.0"},
            "IncomingTraffic": {"Name": "InOctets", "ObjectId": "1.3.6.1.2.1.2.2.1.10.1"},
        }
    elif protocol == "J1939":
        base_config[f"{protocol}-SOURCE"]["AdapterNetwork"] = "CAN-NETWORK-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "EngineSpeed": {"Name": "RPM", "PGN": 61444, "SPNs": [190]},
            "EngineTemp": {"Name": "Temperature", "PGN": 65262, "SPNs": [110]},
        }
    elif protocol == "NATS":
        base_config[f"{protocol}-SOURCE"]["AdapterBroker"] = "NATS-SERVER-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "SensorData": {"Subject": "sensors.data"},
            "AlarmEvents": {"Subject": "alarms.events"},
        }
    elif protocol == "OPCDA":
        base_config[f"{protocol}-SOURCE"]["AdapterServer"] = "OPCDA-SERVER-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Temperature": {"ItemId": "Device1.Temperature"},
            "Pressure": {"ItemId": "Device1.Pressure"},
        }
    elif protocol == "PCCC":
        base_config[f"{protocol}-SOURCE"]["AdapterController"] = "PCCC-CONTROLLER-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Counter": {"Name": "ProductCounter", "Address": "N7:0"},
            "Status": {"Name": "MachineStatus", "Address": "B3:0/0"},
        }
    elif protocol == "SIMULATOR":
        base_config[f"{protocol}-SOURCE"]["Channels"] = { 
            "counter": {"Simulation": {"SimulationType": "Counter", "DataType": "Int", "Min": 0, "Max": 100}},
            "sinus": {"Simulation": {"SimulationType": "Sinus", "DataType": "Byte", "Min": 0, "Max": 100}},
            "triangle": {"Simulation": {"SimulationType": "Triangle", "DataType": "Byte", "Min": 0, "Max": 100}}
        }
    elif protocol == "SLMP":
        base_config[f"{protocol}-SOURCE"]["AdapterController"] = "SLMP-CONTROLLER-1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "DataRegister": {"Name": "Register", "Address": "D100", "Type": "Word"},
            "BitDevice": {"Name": "Status", "Address": "M0", "Type": "Bit"},
        }
    elif protocol == "SQL":
        base_config[f"{protocol}-SOURCE"]["AdapterDatabase"] = "SQL-DB-1"
        base_config[f"{protocol}-SOURCE"]["Query"] = "SELECT temperature, pressure, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1"
        base_config[f"{protocol}-SOURCE"]["Channels"] = {
            "Temperature": {"Name": "Temperature", "ColumnName": "temperature"},
            "Pressure": {"Name": "Pressure", "ColumnName": "pressure"},
        }

    return base_config


def generate_target_template(
    target: str, environment: str, sfc_knowledge: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate target configuration template

    Args:
        target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
        environment: Environment type (development, production)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing target configuration
    """
    base_config = {f"{target}Target": {"Active": True, "TargetType": target}}

    # Add target-specific configurations
    if target == "AWS-S3":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "BucketName": "sfc-data-bucket",
                "Interval": 60,
                "BufferSize": 10,
                "Prefix": "industrial-data",
                "Compression": "Gzip" if environment == "production" else "None",
            }
        )
    elif target == "AWS-IOT-CORE":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1", 
                "TopicName": "sfc/industrial-data",
                "BatchSize": 1024,
                "BatchCount": 100,
                "BatchInterval": 5000 if environment == "production" else 1000,
            }
        )
    elif target == "AWS-LAMBDA":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "FunctionName": "sfc-data-processor",
                "BatchSize": 50,
                "Interval": 1000,
            }
        )
    elif target == "AWS-KINESIS":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "StreamName": "sfc-data-stream",
                "BatchSize": 500,
                "Interval": 1000,
            }
        )
    elif target == "AWS-KINESIS-FIREHOSE":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "DeliveryStreamName": "sfc-delivery-stream",
                "BatchSize": 500,
                "Interval": 1000,
            }
        )
    elif target == "AWS-S3-TABLES":
        base_config[f"{target}Target"].update(
           {
                "Region": "us-east-1",
                "TableBucket": "sfc-data-tables-bucket",
                "Interval": 60,
                "BufferCount": 100,
                "Namespace": "sfc",
                "AutoCreate": True,
                "Tables": [
                    {
                        "TableName": "sfc_table",
                        "Schema": [],
                        "Mappings": [],
                        "Partition": {}
                    }
                ]
            }
        )
    elif target == "AWS-IOT-ANALYTICS":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "ChannelName": "sfc-data-channel",
                "BatchSize": 100,
                "Interval": 1000,
            }
        )
    elif target == "AWS-SITEWISE":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "BatchSize": 10,
                "Interval": 1000,
                "PropertyAliases": {
                    "${source}": "${source}.${channel}"
                },
            }
        )
    elif target == "AWS-SITEWISEEDGE":
        base_config[f"{target}Target"].update(
            {
                "EndPoint": "localhost",
                "Port": 50001,
                "BatchSize": 10,
                "Interval": 1000,
                "PropertyAliases": {
                    "${source}": "${source}.${channel}"
                },
            }
        )
    elif target == "AWS-SNS":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "TopicArn": "arn:aws:sns:us-east-1:123456789012:sfc-notifications",
                "BatchSize": 10,
                "Interval": 1000,
            }
        )
    elif target == "AWS-SQS":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/sfc-data-queue",
                "BatchSize": 10,
                "Interval": 1000,
            }
        )
    elif target == "AWS-TIMESTREAM":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "DatabaseName": "sfc-database",
                "TableName": "sfc-data-table",
                "BatchSize": 100,
                "Interval": 1000,
            }
        )
    elif target == "AWS-MSK":
        base_config[f"{target}Target"].update(
            {
                "Region": "us-east-1",
                "BootstrapServers": "b-1.sfc-msk-cluster.xxxxx.c1.kafka.us-east-1.amazonaws.com:9094,b-2.sfc-msk-cluster.xxxxx.c1.kafka.us-east-1.amazonaws.com:9094",
                "Topic": "sfc-data-topic",
                "BatchSize": 100,
                "Interval": 1000,
                "SecurityProtocol": "SASL_SSL",
            }
        )
    elif target == "DEBUG":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "DEBUG-TARGET",
        }
    elif target == "FILE":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "FILE-TARGET",
            "Directory": "./data",
            "FilenameTemplate": "data-%timestamp%.json",
            "Interval": 60,
            "BufferSize": 10,
        }
    elif target == "MQTT":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "MQTT-TARGET",
            "EndPoint": "localhost",
            "Port": 1883,
            "TopicName": "sfc/data",
            "QoS": 1,
            "ConnectionTimeout": 30000,
        }
    elif target == "NATS":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "NATS-TARGET",
            "EndPoint": "localhost",
            "Port": 4222,
            "Subject": "sfc.data",
        }
    elif target == "OPCUA":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "OPCUA-TARGET",
            "EndPoint": "opc.tcp://localhost:4840",
            "NodeNames": {
                "Temperature": "ns=2;s=Temperature",
                "Pressure": "ns=2;s=Pressure",
            }
        }
    elif target == "OPCUA-WRITER":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "OPCUA-WRITER",
            "EndPoint": "opc.tcp://localhost:4840",
            "NodeIds": {
                "Temperature": "ns=2;s=Temperature",
                "Pressure": "ns=2;s=Pressure",
            }
        }
    elif target == "ROUTER":
        base_config[f"{target}Target"] = {
            "Active": True,
            "TargetType": "ROUTER-TARGET",
            "Routes": [
                {
                    "Name": "Temperature Route",
                    "TargetName": "DEBUG-TARGET",
                    "Condition": "${channel} == 'Temperature'"
                },
                {
                    "Name": "Default Route",
                    "TargetName": "AWS-S3-TARGET"
                }
            ]
        }

    return base_config


def generate_target_types(target: str, sfc_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """Generate target types configuration

    Args:
        target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing target type configuration
    """
    target_types = {}

    # AWS targets
    if target == "AWS-S3":
        target_types["AWS-S3"] = {
            "JarFiles": ["${MODULES_DIR}/aws-s3-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awss3.AwsS3TargetWriter",
        }
    elif target == "AWS-IOT-CORE":
        target_types["AWS-IOT-CORE"] = {
            "JarFiles": ["${MODULES_DIR}/aws-iot-core-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awsiotcore.AwsIotCoreTargetWriter",
        }
    elif target == "AWS-IOT-ANALYTICS":
        target_types["AWS-IOT-ANALYTICS"] = {
            "JarFiles": ["${MODULES_DIR}/aws-iot-analytics-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awsiotanalytics.AwsIotAnalyticsTargetWriter",
        }
    elif target == "AWS-KINESIS":
        target_types["AWS-KINESIS"] = {
            "JarFiles": ["${MODULES_DIR}/aws-kinesis-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awskinesis.AwsKinesisTargetWriter",
        }
    elif target == "AWS-KINESIS-FIREHOSE":
        target_types["AWS-KINESIS-FIREHOSE"] = {
            "JarFiles": ["${MODULES_DIR}/aws-kinesis-firehose-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awskinesisfirehose.AwsKinesisFirehoseTargetWriter",
        }
    elif target == "AWS-S3-TABLES":
        target_types["AWS-S3-TABLES"] = {
            "JarFiles": ["${MODULES_DIR}/aws-s3-tables-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awss3tables.AwsS3TablesTargetWriter",
        }
    elif target == "AWS-LAMBDA":
        target_types["AWS-LAMBDA"] = {
            "JarFiles": ["${MODULES_DIR}/aws-lambda-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awslambda.AwsLambdaTargetWriter",
        }
    elif target == "AWS-MSK":
        target_types["AWS-MSK"] = {
            "JarFiles": ["${MODULES_DIR}/aws-msk-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awsmsk.AwsMskTargetWriter",
        }
    elif target == "AWS-SITEWISE":
        target_types["AWS-SITEWISE"] = {
            "JarFiles": ["${MODULES_DIR}/aws-sitewise-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awssitewise.AwsSitewiseTargetWriter",
        }
    elif target == "AWS-SITEWISEEDGE":
        target_types["AWS-SITEWISEEDGE"] = {
            "JarFiles": ["${MODULES_DIR}/aws-sitewise-edge-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awssitewiseedge.AwsSitewiseEdgeTargetWriter",
        }
    elif target == "AWS-SNS":
        target_types["AWS-SNS"] = {
            "JarFiles": ["${MODULES_DIR}/aws-sns-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awssns.AwsSnsTargetWriter",
        }
    elif target == "AWS-SQS":
        target_types["AWS-SQS"] = {
            "JarFiles": ["${MODULES_DIR}/aws-sqs-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awssqs.AwsSqsTargetWriter",
        }
    elif target == "AWS-TIMESTREAM":
        target_types["AWS-TIMESTREAM"] = {
            "JarFiles": ["${MODULES_DIR}/aws-timestream-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.awstimestream.AwsTimestreamTargetWriter",
        }
        
    # Edge targets
    elif target == "DEBUG":
        target_types["DEBUG-TARGET"] = {
            "JarFiles": ["${MODULES_DIR}/debug-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.debugtarget.DebugTargetWriter",
        }
    elif target == "FILE":
        target_types["FILE-TARGET"] = {
            "JarFiles": ["${MODULES_DIR}/file-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.filetarget.FileTargetWriter",
        }
    elif target == "MQTT":
        target_types["MQTT-TARGET"] = {
            "JarFiles": ["${MODULES_DIR}/mqtt-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.mqtt.MqttTargetWriter",
        }
    elif target == "NATS":
        target_types["NATS-TARGET"] = {
            "JarFiles": ["${MODULES_DIR}/nats-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.nats.NatsTargetWriter",
        }
    elif target == "OPCUA":
        target_types["OPCUA-TARGET"] = {
            "JarFiles": ["${MODULES_DIR}/opcua-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaTargetWriter",
        }
    elif target == "OPCUA-WRITER":
        target_types["OPCUA-WRITER"] = {
            "JarFiles": ["${MODULES_DIR}/opcua-writer/lib"],
            "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaWriter",
        }
    elif target == "ROUTER":
        target_types["ROUTER-TARGET"] = {
            "JarFiles": ["${MODULES_DIR}/router-target/lib"],
            "FactoryClassName": "com.amazonaws.sfc.router.RouterTargetWriter",
        }

    return target_types


def generate_adapter_types(protocol: str, sfc_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """Generate adapter types configuration

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing adapter type configuration
    """
    adapter_types = {}

    if protocol == "OPCUA":
        adapter_types["OPCUA"] = {
            "JarFiles": ["${MODULES_DIR}/opcua/lib"],
            "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaAdapter",
        }
    elif protocol == "MODBUS":
        adapter_types["MODBUS"] = {
            "JarFiles": ["${MODULES_DIR}/modbus/lib"],
            "FactoryClassName": "com.amazonaws.sfc.modbus.ModbusAdapter",
        }
    elif protocol == "S7":
        adapter_types["S7"] = {
            "JarFiles": ["${MODULES_DIR}/s7/lib"],
            "FactoryClassName": "com.amazonaws.sfc.s7.S7Adapter",
        }
    elif protocol == "ADS":
        adapter_types["ADS"] = {
            "JarFiles": ["${MODULES_DIR}/ads/lib"],
            "FactoryClassName": "com.amazonaws.sfc.ads.AdsAdapter",
        }
    elif protocol == "J1939":
        adapter_types["J1939"] = {
            "JarFiles": ["${MODULES_DIR}/j1939/lib"],
            "FactoryClassName": "com.amazonaws.sfc.j1939.J1939Adapter",
        }
    elif protocol == "MQTT":
        adapter_types["MQTT"] = {
            "JarFiles": ["${MODULES_DIR}/mqtt/lib"],
            "FactoryClassName": "com.amazonaws.sfc.mqtt.MqttAdapter",
        }
    elif protocol == "NATS":
        adapter_types["NATS"] = {
            "JarFiles": ["${MODULES_DIR}/nats/lib"],
            "FactoryClassName": "com.amazonaws.sfc.nats.NatsAdapter",
        }
    elif protocol == "OPCDA":
        adapter_types["OPCDA"] = {
            "JarFiles": ["${MODULES_DIR}/opcda/lib"],
            "FactoryClassName": "com.amazonaws.sfc.opcda.OpcdaAdapter",
        }
    elif protocol == "PCCC":
        adapter_types["PCCC"] = {
            "JarFiles": ["${MODULES_DIR}/pccc/lib"],
            "FactoryClassName": "com.amazonaws.sfc.pccc.PcccAdapter",
        }
    elif protocol == "REST":
        adapter_types["REST"] = {
            "JarFiles": ["${MODULES_DIR}/rest/lib"],
            "FactoryClassName": "com.amazonaws.sfc.rest.RestAdapter",
        }
    elif protocol == "SIMULATOR":
        adapter_types["SIMULATOR"] = {
            "JarFiles": ["${MODULES_DIR}/simulator/lib"],
            "FactoryClassName": "com.amazonaws.sfc.simulator.SimulatorAdapter",
        }
    elif protocol == "SLMP":
        adapter_types["SLMP"] = {
            "JarFiles": ["${MODULES_DIR}/slmp/lib"],
            "FactoryClassName": "com.amazonaws.sfc.slmp.SlmpAdapter",
        }
    elif protocol == "SNMP":
        adapter_types["SNMP"] = {
            "JarFiles": ["${MODULES_DIR}/snmp/lib"],
            "FactoryClassName": "com.amazonaws.sfc.snmp.SnmpAdapter",
        }
    elif protocol == "SQL":
        adapter_types["SQL"] = {
            "JarFiles": ["${MODULES_DIR}/sql/lib"],
            "FactoryClassName": "com.amazonaws.sfc.sql.SqlAdapter",
        }

    return adapter_types


def generate_protocol_adapter_config(protocol: str, sfc_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """Generate protocol adapter configuration

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing protocol adapter configuration
    """
    config = {}

    if protocol == "OPCUA":
        config["OPCUA"] = {
            "AdapterType": "OPCUA",
            "OpcuaServers": {
                "OPCUA-SERVER-1": {
                    "Address": "opc.tcp://localhost",
                    "Port": 4840,
                    "Path": "/",
                    "ConnectTimeout": 10000,
                    "ReadBatchSize": 500,
                }
            },
        }
    elif protocol == "MODBUS":
        config["MODBUS"] = {
            "AdapterType": "MODBUS",
            "Controllers": {
                "MODBUS-CONTROLLER-1": {
                    "Address": "192.168.1.100",
                    "Port": 502,
                    "UnitId": 1,
                }
            },
        }
    elif protocol == "S7":
        config["S7"] = {
            "AdapterType": "S7",
            "Controllers": {
                "S7-PLC-1": {
                    "Address": "192.168.1.130",
                    "ControllerType": "S7-1200",
                }
            },
        }
    elif protocol == "ADS":
        config["ADS"] = {
            "AdapterType": "ADS",
            "Controllers": {
                "ADS-CONTROLLER-1": {
                    "Address": "192.168.1.140",
                    "Port": 48898,
                    "ConnectTimeout": 10000,
                }
            },
        }
    elif protocol == "J1939":
        config["J1939"] = {
            "AdapterType": "J1939",
            "Networks": {
                "CAN-NETWORK-1": {
                    "Interface": "can0",
                    "PollInterval": 500,
                }
            },
        }
    elif protocol == "MQTT":
        config["MQTT"] = {
            "AdapterType": "MQTT",
            "Brokers": {
                "MQTT-BROKER-1": {
                    "EndPoint": "localhost",
                    "Port": 1883,
                    "ConnectionTimeout": 10,
                }
            },
            "ReadMode": "KeepLast",
        }
    elif protocol == "NATS":
        config["NATS"] = {
            "AdapterType": "NATS",
            "Brokers": {
                "NATS-SERVER-1": {
                    "EndPoint": "localhost",
                    "Port": 4222,
                }
            },
        }
    elif protocol == "OPCDA":
        config["OPCDA"] = {
            "AdapterType": "OPCDA",
            "Servers": {
                "OPCDA-SERVER-1": {
                    "Host": "localhost",
                    "ProgID": "Matrikon.OPC.Simulation",
                    "ConnectTimeout": 5000,
                }
            },
        }
    elif protocol == "PCCC":
        config["PCCC"] = {
            "AdapterType": "PCCC",
            "Controllers": {
                "PCCC-CONTROLLER-1": {
                    "Address": "192.168.1.150",
                    "Port": 44818,
                }
            },
        }
    elif protocol == "REST":
        config["REST"] = {
            "AdapterType": "REST",
            "Endpoints": {
                "REST-ENDPOINT-1": {
                    "BaseUrl": "http://localhost:8080/api",
                    "ConnectTimeout": 5000,
                }
            },
        }
    elif protocol == "SIMULATOR":
        config["SIMULATOR"] = {
            "AdapterType": "SIMULATOR",
        }
    elif protocol == "SLMP":
        config["SLMP"] = {
            "AdapterType": "SLMP",
            "Controllers": {
                "SLMP-CONTROLLER-1": {
                    "Address": "192.168.1.160",
                    "Port": 5007,
                    "ConnectTimeout": 5000,
                }
            },
        }
    elif protocol == "SNMP":
        config["SNMP"] = {
            "AdapterType": "SNMP",
            "Devices": {
                "SNMP-DEVICE-1": {
                    "Address": "192.168.1.170",
                    "Port": 161,
                    "Version": "V2c",
                    "Community": "public",
                }
            },
        }
    elif protocol == "SQL":
        config["SQL"] = {
            "AdapterType": "SQL",
            "Databases": {
                "SQL-DB-1": {
                    "ConnectionString": "jdbc:mysql://localhost:3306/testdb",
                    "Driver": "com.mysql.jdbc.Driver",
                    "Username": "${DB_USER}",
                    "Password": "${DB_PASSWORD}",
                }
            },
        }

    return config
