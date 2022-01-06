-- DROP SCHEMA "PROD_001";

CREATE SCHEMA "PROD_001" AUTHORIZATION postgres;

-- DROP SEQUENCE "PROD_001"."SEQ_ACA_ID";

CREATE SEQUENCE "PROD_001"."SEQ_ACA_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_AEA_ID";

CREATE SEQUENCE "PROD_001"."SEQ_AEA_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_ALC_ID";

CREATE SEQUENCE "PROD_001"."SEQ_ALC_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_ALR_ID";

CREATE SEQUENCE "PROD_001"."SEQ_ALR_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_AMA_ID";

CREATE SEQUENCE "PROD_001"."SEQ_AMA_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_BAL_ID";

CREATE SEQUENCE "PROD_001"."SEQ_BAL_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_CUP_ID";

CREATE SEQUENCE "PROD_001"."SEQ_CUP_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_CUR_ID";

CREATE SEQUENCE "PROD_001"."SEQ_CUR_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_ECP_ID";

CREATE SEQUENCE "PROD_001"."SEQ_ECP_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_EXC_ID";

CREATE SEQUENCE "PROD_001"."SEQ_EXC_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_LAL_ID";

CREATE SEQUENCE "PROD_001"."SEQ_LAL_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_MCP_ID";

CREATE SEQUENCE "PROD_001"."SEQ_MCP_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_MED_ID";

CREATE SEQUENCE "PROD_001"."SEQ_MED_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_PEL_ID";

CREATE SEQUENCE "PROD_001"."SEQ_PEL_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_SYL_ID";

CREATE SEQUENCE "PROD_001"."SEQ_SYL_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_TRF_ID";

CREATE SEQUENCE "PROD_001"."SEQ_TRF_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE "PROD_001"."SEQ_UNI_ID";

CREATE SEQUENCE "PROD_001"."SEQ_UNI_ID"
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;-- "PROD_001"."ALGO_REGISTRY" definition

-- Drop table

-- DROP TABLE "PROD_001"."ALGO_REGISTRY";

CREATE TABLE "PROD_001"."ALGO_REGISTRY" (
	"ALR_ID" int4 NOT NULL,
	"ALR_NAME" varchar NOT NULL,
	"ALR_DESCRIPTION" varchar NOT NULL,
	"ALR_STATUS" varchar NOT NULL,
	CONSTRAINT "ALGO_REGISTRY_pkey" PRIMARY KEY ("ALR_ID")
);


-- "PROD_001"."CURRENCY" definition

-- Drop table

-- DROP TABLE "PROD_001"."CURRENCY";

CREATE TABLE "PROD_001"."CURRENCY" (
	"CUR_ID" int4 NOT NULL,
	"CUR_CODE" varchar NOT NULL,
	"CUR_TYPE" varchar NOT NULL,
	CONSTRAINT "CURRENCY_pkey" PRIMARY KEY ("CUR_ID")
);


-- "PROD_001"."EXCHANGE" definition

-- Drop table

-- DROP TABLE "PROD_001"."EXCHANGE";

CREATE TABLE "PROD_001"."EXCHANGE" (
	"EXC_ID" int4 NOT NULL,
	"EXC_NAME" varchar NOT NULL,
	CONSTRAINT "EXCHANGE_pkey" PRIMARY KEY ("EXC_ID")
);


-- "PROD_001"."LATENCY_LOG" definition

-- Drop table

-- DROP TABLE "PROD_001"."LATENCY_LOG";

CREATE TABLE "PROD_001"."LATENCY_LOG" (
	"LAL_ID" int8 NOT NULL,
	"LAL_TIMESTAMP" timestamptz NOT NULL,
	"LAL_TYPE" varchar NOT NULL,
	"LAL_ORL_ID" uuid NULL,
	"LAL_VALUE" int4 NULL,
	CONSTRAINT "LATENCY_LOG_pkey" PRIMARY KEY ("LAL_ID")
);


-- "PROD_001"."METRIC_DEFINITION" definition

-- Drop table

-- DROP TABLE "PROD_001"."METRIC_DEFINITION";

CREATE TABLE "PROD_001"."METRIC_DEFINITION" (
	"MED_ID" int4 NOT NULL,
	"MED_NAME" varchar NOT NULL,
	"MED_DESCRIPTION" varchar NOT NULL,
	"MED_CLASS_NAME" varchar NOT NULL,
	CONSTRAINT "METRIC_DEFINITION_pkey" PRIMARY KEY ("MED_ID")
);


-- "PROD_001"."SYSTEM_LOG" definition

-- Drop table

-- DROP TABLE "PROD_001"."SYSTEM_LOG";

CREATE TABLE "PROD_001"."SYSTEM_LOG" (
	"SYL_ID" int8 NOT NULL,
	"SYL_ENTITY_NAME" varchar NOT NULL,
	"SYL_ORL_ID" uuid NULL,
	"SYL_TIMESTAMP" timestamptz NOT NULL,
	"SYL_LEVEL" varchar NOT NULL,
	"SYL_FILE" varchar NOT NULL,
	"SYL_FUNCTION" varchar NOT NULL,
	"SYL_LINE_NO" int4 NOT NULL,
	"SYL_MESSAGE" varchar NOT NULL,
	CONSTRAINT "SYSTEM_LOG_pkey" PRIMARY KEY ("SYL_ID")
);


-- "PROD_001"."UNITS" definition

-- Drop table

-- DROP TABLE "PROD_001"."UNITS";

CREATE TABLE "PROD_001"."UNITS" (
	"UNI_ID" int4 NOT NULL,
	"UNI_SYMBOL" varchar NOT NULL,
	"UNI_DESCRIPTION" varchar NULL,
	CONSTRAINT "UNITS_pkey" PRIMARY KEY ("UNI_ID")
);


-- "PROD_001"."ALGO_CONFIGURATION" definition

-- Drop table

-- DROP TABLE "PROD_001"."ALGO_CONFIGURATION";

CREATE TABLE "PROD_001"."ALGO_CONFIGURATION" (
	"ALC_ID" int4 NOT NULL,
	"ALC_ALR_ID" int4 NOT NULL,
	"ALC_NAME" varchar NOT NULL,
	"ALC_VALUE" varchar NOT NULL,
	CONSTRAINT "ALGO_CONFIGURATION_pkey" PRIMARY KEY ("ALC_ID"),
	CONSTRAINT "ALGO_CONFIGURATION_ALC_ALR_ID_fkey" FOREIGN KEY ("ALC_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID")
);


-- "PROD_001"."ALGO_EXCHANGE_ASSOCIATION" definition

-- Drop table

-- DROP TABLE "PROD_001"."ALGO_EXCHANGE_ASSOCIATION";

CREATE TABLE "PROD_001"."ALGO_EXCHANGE_ASSOCIATION" (
	"AEA_ID" int4 NOT NULL,
	"AEA_ALR_ID" int4 NOT NULL,
	"AEA_EXC_ID" int4 NOT NULL,
	CONSTRAINT "ALGO_EXCHANGE_ASSOCIATION_pkey" PRIMARY KEY ("AEA_ID"),
	CONSTRAINT "ALGO_EXCHANGE_ASSOCIATION_AEA_ALR_ID_fkey" FOREIGN KEY ("AEA_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "ALGO_EXCHANGE_ASSOCIATION_AEA_EXC_ID_fkey" FOREIGN KEY ("AEA_EXC_ID") REFERENCES "PROD_001"."EXCHANGE"("EXC_ID")
);


-- "PROD_001"."ALGO_METRIC_ASSOCIATION" definition

-- Drop table

-- DROP TABLE "PROD_001"."ALGO_METRIC_ASSOCIATION";

CREATE TABLE "PROD_001"."ALGO_METRIC_ASSOCIATION" (
	"AMA_ID" int4 NOT NULL,
	"AMA_ALR_ID" int4 NOT NULL,
	"AMA_MED_ID" int4 NOT NULL,
	CONSTRAINT "ALGO_METRIC_ASSOCIATION_pkey" PRIMARY KEY ("AMA_ID"),
	CONSTRAINT "ALGO_METRIC_ASSOCIATION_AMA_ALR_ID_fkey" FOREIGN KEY ("AMA_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "ALGO_METRIC_ASSOCIATION_AMA_MED_ID_fkey" FOREIGN KEY ("AMA_MED_ID") REFERENCES "PROD_001"."METRIC_DEFINITION"("MED_ID")
);


-- "PROD_001"."BALANCE" definition

-- Drop table

-- DROP TABLE "PROD_001"."BALANCE";

CREATE TABLE "PROD_001"."BALANCE" (
	"BAL_ID" int8 NOT NULL,
	"BAL_TIMESTAMP" timestamptz NOT NULL,
	"BAL_ALR_ID" int4 NOT NULL,
	"BAL_EXC_ID" int4 NOT NULL,
	"BAL_CUR_ID" int4 NOT NULL,
	"BAL_AMOUNT" float8 NOT NULL,
	"BAL_QUOTE_PRICE" float8 NOT NULL,
	"BAL_QUOTE_CURRENCY" int4 NOT NULL,
	CONSTRAINT "BALANCE_pkey" PRIMARY KEY ("BAL_ID"),
	CONSTRAINT "BALANCE_BAL_ALR_ID_fkey" FOREIGN KEY ("BAL_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "BALANCE_BAL_CUR_ID_fkey" FOREIGN KEY ("BAL_CUR_ID") REFERENCES "PROD_001"."CURRENCY"("CUR_ID"),
	CONSTRAINT "BALANCE_BAL_EXC_ID_fkey" FOREIGN KEY ("BAL_EXC_ID") REFERENCES "PROD_001"."EXCHANGE"("EXC_ID"),
	CONSTRAINT "BALANCE_BAL_QUOTE_CURRENCY_fkey" FOREIGN KEY ("BAL_QUOTE_CURRENCY") REFERENCES "PROD_001"."CURRENCY"("CUR_ID")
);


-- "PROD_001"."CURRENCY_PAIR" definition

-- Drop table

-- DROP TABLE "PROD_001"."CURRENCY_PAIR";

CREATE TABLE "PROD_001"."CURRENCY_PAIR" (
	"CUP_ID" int4 NOT NULL,
	"CUP_CUR_ID_BASE" int4 NOT NULL,
	"CUP_CUR_ID_QUOTE" int4 NOT NULL,
	"CUP_CODE" varchar NOT NULL,
	CONSTRAINT "CURRENCY_PAIR_pkey" PRIMARY KEY ("CUP_ID"),
	CONSTRAINT "CURRENCY_PAIR_CUP_CUR_ID_BASE_fkey" FOREIGN KEY ("CUP_CUR_ID_BASE") REFERENCES "PROD_001"."CURRENCY"("CUR_ID"),
	CONSTRAINT "CURRENCY_PAIR_CUP_CUR_ID_QUOTE_fkey" FOREIGN KEY ("CUP_CUR_ID_QUOTE") REFERENCES "PROD_001"."CURRENCY"("CUR_ID")
);


-- "PROD_001"."EXCHANGE_CURRENCY_PAIR" definition

-- Drop table

-- DROP TABLE "PROD_001"."EXCHANGE_CURRENCY_PAIR";

CREATE TABLE "PROD_001"."EXCHANGE_CURRENCY_PAIR" (
	"ECP_ID" int4 NOT NULL,
	"ECP_EXC_ID" int4 NOT NULL,
	"ECP_CUP_ID" int4 NOT NULL,
	"ECP_BASE_PREC" float8 NULL,
	"ECP_QUOTE_PREC" float8 NULL,
	"ECP_MIN_QTY" float8 NULL,
	"ECP_STEPSIZE" float8 NULL,
	CONSTRAINT "EXCHANGE_CURRENCY_PAIR_pkey" PRIMARY KEY ("ECP_ID"),
	CONSTRAINT "EXCHANGE_CURRENCY_PAIR_ECP_CUP_ID_fkey" FOREIGN KEY ("ECP_CUP_ID") REFERENCES "PROD_001"."CURRENCY_PAIR"("CUP_ID"),
	CONSTRAINT "EXCHANGE_CURRENCY_PAIR_ECP_EXC_ID_fkey" FOREIGN KEY ("ECP_EXC_ID") REFERENCES "PROD_001"."EXCHANGE"("EXC_ID")
);


-- "PROD_001"."METRIC_CLASS_PARAMETER" definition

-- Drop table

-- DROP TABLE "PROD_001"."METRIC_CLASS_PARAMETER";

CREATE TABLE "PROD_001"."METRIC_CLASS_PARAMETER" (
	"MCP_ID" int4 NOT NULL,
	"MCP_MED_ID" int4 NOT NULL,
	"MCP_NAME" varchar NOT NULL,
	"MCP_VALUE" varchar NOT NULL,
	CONSTRAINT "METRIC_CLASS_PARAMETER_pkey" PRIMARY KEY ("MCP_ID"),
	CONSTRAINT "METRIC_CLASS_PARAMETER_MCP_MED_ID_fkey" FOREIGN KEY ("MCP_MED_ID") REFERENCES "PROD_001"."METRIC_DEFINITION"("MED_ID")
);


-- "PROD_001"."ORDER_LOG" definition

-- Drop table

-- DROP TABLE "PROD_001"."ORDER_LOG";

CREATE TABLE "PROD_001"."ORDER_LOG" (
	"ORL_ID" uuid NOT NULL,
	"ORL_ALR_ID" int4 NOT NULL,
	"ORL_EXC_ID" int4 NOT NULL,
	"ORL_CUP_ID" int4 NOT NULL,
	"ORL_COMBO_ID" varchar NULL,
	"ORL_TIMESTAMP" timestamptz NOT NULL,
	"ORL_QUANTITY" float8 NOT NULL,
	"ORL_PRICE" float8 NOT NULL,
	"ORL_DIRECTION" varchar NOT NULL,
	"ORL_TYPE" varchar NOT NULL,
	"ORL_Q_FILLED" float8 NOT NULL,
	"ORL_STATUS" varchar NOT NULL,
	"ORL_FEE" float8 NOT NULL,
	"ORL_FEE_CURRENCY" int4 NOT NULL,
	CONSTRAINT "ORDER_LOG_pkey" PRIMARY KEY ("ORL_ID"),
	CONSTRAINT "ORDER_LOG_ORL_ALR_ID_fkey" FOREIGN KEY ("ORL_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "ORDER_LOG_ORL_CUP_ID_fkey" FOREIGN KEY ("ORL_CUP_ID") REFERENCES "PROD_001"."CURRENCY_PAIR"("CUP_ID"),
	CONSTRAINT "ORDER_LOG_ORL_EXC_ID_fkey" FOREIGN KEY ("ORL_EXC_ID") REFERENCES "PROD_001"."EXCHANGE"("EXC_ID"),
	CONSTRAINT "ORDER_LOG_ORL_FEE_CURRENCY_fkey" FOREIGN KEY ("ORL_FEE_CURRENCY") REFERENCES "PROD_001"."CURRENCY"("CUR_ID")
);


-- "PROD_001"."PERFORMANCE_LOG" definition

-- Drop table

-- DROP TABLE "PROD_001"."PERFORMANCE_LOG";

CREATE TABLE "PROD_001"."PERFORMANCE_LOG" (
	"PEL_ID" int8 NOT NULL,
	"PEL_ALR_ID" int4 NOT NULL,
	"PEL_MED_ID" int4 NOT NULL,
	"PEL_UNI_ID" int4 NOT NULL,
	"PEL_TIMESTAMP" timestamptz NOT NULL,
	"PEL_VALUE" float8 NOT NULL,
	CONSTRAINT "PERFORMANCE_LOG_pkey" PRIMARY KEY ("PEL_ID"),
	CONSTRAINT "PERFORMANCE_LOG_PEL_ALR_ID_fkey" FOREIGN KEY ("PEL_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "PERFORMANCE_LOG_PEL_MED_ID_fkey" FOREIGN KEY ("PEL_MED_ID") REFERENCES "PROD_001"."METRIC_DEFINITION"("MED_ID"),
	CONSTRAINT "PERFORMANCE_LOG_PEL_UNI_ID_fkey" FOREIGN KEY ("PEL_UNI_ID") REFERENCES "PROD_001"."UNITS"("UNI_ID")
);


-- "PROD_001"."TRANSFERS" definition

-- Drop table

-- DROP TABLE "PROD_001"."TRANSFERS";

CREATE TABLE "PROD_001"."TRANSFERS" (
	"TRF_ID" int8 NOT NULL,
	"TRF_ALR_ID" int4 NOT NULL,
	"TRF_EXC_ID_IN" int4 NOT NULL,
	"TRF_EXC_ID_OUT" int4 NOT NULL,
	"TRF_CUR_ID" int4 NOT NULL,
	"TRF_TIMESTAMP" timestamptz NOT NULL,
	"TRF_AMOUNT" float8 NOT NULL,
	CONSTRAINT "TRANSFERS_pkey" PRIMARY KEY ("TRF_ID"),
	CONSTRAINT "TRANSFERS_TRF_ALR_ID_fkey" FOREIGN KEY ("TRF_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "TRANSFERS_TRF_CUR_ID_fkey" FOREIGN KEY ("TRF_CUR_ID") REFERENCES "PROD_001"."CURRENCY"("CUR_ID"),
	CONSTRAINT "TRANSFERS_TRF_EXC_ID_IN_fkey" FOREIGN KEY ("TRF_EXC_ID_IN") REFERENCES "PROD_001"."EXCHANGE"("EXC_ID"),
	CONSTRAINT "TRANSFERS_TRF_EXC_ID_OUT_fkey" FOREIGN KEY ("TRF_EXC_ID_OUT") REFERENCES "PROD_001"."EXCHANGE"("EXC_ID")
);


-- "PROD_001"."ALGO_CURRENCY_ASSOCIATION" definition

-- Drop table

-- DROP TABLE "PROD_001"."ALGO_CURRENCY_ASSOCIATION";

CREATE TABLE "PROD_001"."ALGO_CURRENCY_ASSOCIATION" (
	"ACA_ID" int4 NOT NULL,
	"ACA_ALR_ID" int4 NOT NULL,
	"ACA_CUP_ID" int4 NOT NULL,
	CONSTRAINT "ALGO_CURRENCY_ASSOCIATION_pkey" PRIMARY KEY ("ACA_ID"),
	CONSTRAINT "ALGO_CURRENCY_ASSOCIATION_ACA_ALR_ID_fkey" FOREIGN KEY ("ACA_ALR_ID") REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID"),
	CONSTRAINT "ALGO_CURRENCY_ASSOCIATION_ACA_CUP_ID_fkey" FOREIGN KEY ("ACA_CUP_ID") REFERENCES "PROD_001"."CURRENCY_PAIR"("CUP_ID")
);