--
-- PostgreSQL database dump
--

\restrict TT31fbgce9XaL8lmFRMsJbxGvRyv8IEfAHpWoX2CyyNyNXile68mk6sqwvoZe6p

-- Dumped from database version 18.6 (Debian 18.6-1.pgdg13+2)
-- Dumped by pg_dump version 18.6 (Debian 18.6-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: action_items; Type: TABLE; Schema: public; Owner: salas
--

CREATE TABLE public.action_items (
    id integer NOT NULL,
    action_key character varying(200) NOT NULL,
    type character varying(50) NOT NULL,
    property_id integer,
    month character varying(7) NOT NULL,
    message character varying(500) NOT NULL,
    status character varying(20) DEFAULT 'open'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    resolved_at timestamp without time zone
);


ALTER TABLE public.action_items OWNER TO salas;

--
-- Name: action_items_id_seq; Type: SEQUENCE; Schema: public; Owner: salas
--

CREATE SEQUENCE public.action_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.action_items_id_seq OWNER TO salas;

--
-- Name: action_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salas
--

ALTER SEQUENCE public.action_items_id_seq OWNED BY public.action_items.id;


--
-- Name: all_expenses; Type: TABLE; Schema: public; Owner: salas
--

CREATE TABLE public.all_expenses (
    id integer NOT NULL,
    date character varying(20) NOT NULL,
    bank character varying(50) NOT NULL,
    description character varying(500) NOT NULL,
    debit numeric(12,2),
    credit numeric(12,2),
    category character varying(100),
    overridden boolean DEFAULT false NOT NULL,
    comments character varying(2000),
    property_id integer,
    vehicle_id integer,
    receipt_filename character varying(500),
    balanced_date character varying(10),
    amortize_months integer,
    amortize_start_date character varying(10)
);


ALTER TABLE public.all_expenses OWNER TO salas;

--
-- Name: all_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: salas
--

CREATE SEQUENCE public.all_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.all_expenses_id_seq OWNER TO salas;

--
-- Name: all_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salas
--

ALTER SEQUENCE public.all_expenses_id_seq OWNED BY public.all_expenses.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: salas
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    keywords text DEFAULT '[]'::text NOT NULL
);


ALTER TABLE public.categories OWNER TO salas;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: salas
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categories_id_seq OWNER TO salas;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salas
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: rental_properties; Type: TABLE; Schema: public; Owner: salas
--

CREATE TABLE public.rental_properties (
    id integer NOT NULL,
    alias character varying(100) NOT NULL,
    address character varying(500) NOT NULL,
    tenant character varying(200),
    lease_renewal_date character varying(10),
    payment_day integer
);


ALTER TABLE public.rental_properties OWNER TO salas;

--
-- Name: rental_properties_id_seq; Type: SEQUENCE; Schema: public; Owner: salas
--

CREATE SEQUENCE public.rental_properties_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rental_properties_id_seq OWNER TO salas;

--
-- Name: rental_properties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salas
--

ALTER SEQUENCE public.rental_properties_id_seq OWNED BY public.rental_properties.id;


--
-- Name: vehicle_services; Type: TABLE; Schema: public; Owner: salas
--

CREATE TABLE public.vehicle_services (
    id integer NOT NULL,
    vehicle_id integer NOT NULL,
    date character varying(10) NOT NULL,
    description character varying(500) NOT NULL,
    mileage integer
);


ALTER TABLE public.vehicle_services OWNER TO salas;

--
-- Name: vehicle_services_id_seq; Type: SEQUENCE; Schema: public; Owner: salas
--

CREATE SEQUENCE public.vehicle_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vehicle_services_id_seq OWNER TO salas;

--
-- Name: vehicle_services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salas
--

ALTER SEQUENCE public.vehicle_services_id_seq OWNED BY public.vehicle_services.id;


--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: salas
--

CREATE TABLE public.vehicles (
    id integer NOT NULL,
    alias character varying(100) NOT NULL,
    make character varying(100) NOT NULL,
    model character varying(100) NOT NULL,
    year integer NOT NULL,
    registration_due_date character varying(10)
);


ALTER TABLE public.vehicles OWNER TO salas;

--
-- Name: vehicles_id_seq; Type: SEQUENCE; Schema: public; Owner: salas
--

CREATE SEQUENCE public.vehicles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vehicles_id_seq OWNER TO salas;

--
-- Name: vehicles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salas
--

ALTER SEQUENCE public.vehicles_id_seq OWNED BY public.vehicles.id;


--
-- Name: action_items id; Type: DEFAULT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.action_items ALTER COLUMN id SET DEFAULT nextval('public.action_items_id_seq'::regclass);


--
-- Name: all_expenses id; Type: DEFAULT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.all_expenses ALTER COLUMN id SET DEFAULT nextval('public.all_expenses_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: rental_properties id; Type: DEFAULT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.rental_properties ALTER COLUMN id SET DEFAULT nextval('public.rental_properties_id_seq'::regclass);


--
-- Name: vehicle_services id; Type: DEFAULT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.vehicle_services ALTER COLUMN id SET DEFAULT nextval('public.vehicle_services_id_seq'::regclass);


--
-- Name: vehicles id; Type: DEFAULT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.vehicles ALTER COLUMN id SET DEFAULT nextval('public.vehicles_id_seq'::regclass);


--
-- Data for Name: action_items; Type: TABLE DATA; Schema: public; Owner: salas
--

COPY public.action_items (id, action_key, type, property_id, month, message, status, created_at, resolved_at) FROM stdin;
1	rent_unpaid:1:2026-08	rent_unpaid	1	2026-08	Rent for Escalante hasn't been paid for 2026-08.	open	2026-08-16 22:25:23.95436	\N
2	rent_unpaid:2:2026-08	rent_unpaid	2	2026-08	Rent for Franklin hasn't been paid for 2026-08.	open	2026-08-16 22:25:23.95436	\N
3	rent_unpaid:4:2026-08	rent_unpaid	4	2026-08	Rent for Kostka hasn't been paid for 2026-08.	open	2026-08-16 22:25:23.95436	\N
4	utility_changed:none:Tep Corporate:2026-03	utility_changed	\N	2026-03	Tep Corporate payment changed from $150.34 to $111.90 in 2026-03.	open	2026-08-16 22:25:23.95436	\N
5	utility_changed:none:Southwest Gas:2026-03	utility_changed	\N	2026-03	Southwest Gas payment changed from $80.65 to $103.98 in 2026-03.	open	2026-08-16 22:25:23.95436	\N
6	utility_changed:none:TUCSON WATER:2026-04	utility_changed	\N	2026-04	TUCSON WATER payment changed from $105.24 to $50.02 in 2026-04.	open	2026-08-16 22:25:23.95436	\N
16	utility_changed:none:Tep Corporate:2026-07	utility_changed	\N	2026-07	Tep Corporate payment changed from $170.33 to $192.55 in 2026-07.	open	2026-08-16 23:08:51.149064	\N
17	utility_changed:none:Southwest Gas:2026-07	utility_changed	\N	2026-07	Southwest Gas payment changed from $23.03 to $54.63 in 2026-07.	open	2026-08-16 23:08:51.149064	\N
\.


--
-- Data for Name: all_expenses; Type: TABLE DATA; Schema: public; Owner: salas
--

COPY public.all_expenses (id, date, bank, description, debit, credit, category, overridden, comments, property_id, vehicle_id, receipt_filename, balanced_date, amortize_months, amortize_start_date) FROM stdin;
1322	2025-12-16 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	21.48	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1323	2025-12-16 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	34.14	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1324	2025-12-16 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	271.70	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1325	2025-12-16 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	NaN	27.16	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1327	2025-12-16 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	7.36	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1328	2025-12-17 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	34.34	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1329	2025-12-18 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	NaN	2.18	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1330	2025-12-18 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	NaN	6.51	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1331	2025-12-18 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	NaN	7.60	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1332	2025-12-18 00:00:00	citi	MARSHALLS #1295 TUCSON AZ	27.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1333	2025-12-18 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	35.27	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1334	2025-12-18 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	8.99	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1335	2025-12-18 00:00:00	citi	COT ES LOS REALES SCALES TUCSON AZ	15.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1392	2025-12-18 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	123.06	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1393	2025-12-18 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	2500.00	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1394	2025-12-18 00:00:00	chase	Xoom Debit OID 37456972 Web ID: 1770510487	1000.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1395	2025-12-19 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	2500.00	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1397	2025-12-26 00:00:00	chase	Modular Mining S Payroll PPD ID: 4260302465	NaN	4834.18	Income	f	\N	\N	\N	\N	\N	\N	\N
1398	2025-12-26 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1776.31	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1399	2025-12-29 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1400	2025-12-29 00:00:00	chase	12/29 Online Domestic Wire Transfer Via: Western Alliance/122105980 A/C: Alliance Bank of	2000.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1401	2025-12-29 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	38.70	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1402	2026-01-02 00:00:00	chase	Zelle Payment To Rene Salas 27560839732	70.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1403	2026-01-02 00:00:00	chase	Nsm Dbamr.Cooper Nsm Dbamr 1121073 Web ID: 0000452701	1530.23	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1404	2026-01-02 00:00:00	chase	Zelle Payment To Reyna Maria 27153435690	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
1405	2026-01-02 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4430.31	Income	f	\N	\N	\N	\N	\N	\N	\N
1407	2026-01-05 00:00:00	chase	Zelle Payment From Yesenia Valenzuela 27591588234	NaN	1300.00	Real State	f	\N	\N	\N	\N	\N	\N	\N
1408	2026-01-05 00:00:00	chase	Citi Autopay Payment 291899051270260 Web ID: Citicardap	5235.61	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1409	2026-01-05 00:00:00	chase	Honda Pmt 8004451358 PPD ID: A953472715	625.43	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1411	2026-01-05 00:00:00	chase	01/05 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1412	2026-01-08 00:00:00	chase	Zelle Payment To Karina Gonzalez Jpm99C1Bvcsz	240.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1413	2026-01-12 00:00:00	chase	Zelle Payment To Perro Loco Ajo 27659431575	15.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1415	2026-01-13 00:00:00	chase	Zelle Payment To Francisco Herrera 27688207004	55.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1416	2026-01-14 00:00:00	chase	Zelle Payment To Jesus Encinas (Piso) Jpm99C1Zm0Eh	1500.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1417	2026-01-15 00:00:00	chase	Zelle Payment To Carmen Baray Jpm99C219Y70	200.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1418	2026-01-16 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	77.53	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1419	2026-01-16 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
1420	2026-01-20 00:00:00	chase	Zelle Payment To Ezequiel Pina 27738565594	1000.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1421	2026-01-20 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1422	2026-01-20 00:00:00	chase	Zelle Payment To Francisco Herrera 27757349879	400.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1423	2025-12-18 00:00:00	banamex	PAGO RECIBIDO DE TESORED POR ORDEN DE MANUEL SALAS REF.2658724 43045233400 RASTREO:	NaN	956.76	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1424	2025-12-19 00:00:00	banamex	PAGO INTERBANCARIO A BBVA MEXICO AL BENEF. YASAEL,OCHOA/OCHOA (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 004152314320951380 CLAVE RASTREO 085909811774335356 REF. 0191225 tacos MISMO DIA	31.35	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1406	2026-01-05 00:00:00	chase	01/05 Online Domestic Wire Transfer Via: Western Alliance/122105980 A/C: Alliance Bank of	45521.60	NaN	Transfers	f	Kostka 20% down payment	\N	\N	\N	\N	\N	\N
1451	2026-01-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	32.54	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1452	2026-01-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	45.59	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1453	2026-01-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	46.41	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1773	2026-03-13 00:00:00	citi	REST NINJA RAM GOMEZ M CD JUAREZ CHIMX	62.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1774	2026-03-13 00:00:00	citi	GAS GRUPO PENA COTA AGUA PRIETA SMX	38.69	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1775	2026-03-13 00:00:00	citi	FAR GUAD 1563 JUAREZ CHIH MX	3.49	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1319	2025-12-14 00:00:00	citi	RAISING CANES 0598 TUCSON AZ	37.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1320	2025-12-15 00:00:00	citi	WAL-MART #4490 TUCSON AZ	70.08	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1321	2025-12-15 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	69.47	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1336	2025-12-18 00:00:00	citi	PANDA EXPRESS #3525 TUSCAN AZ	14.24	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1337	2025-12-18 00:00:00	citi	TOMMYS EXPRESS AZ452 161-63698917 AZ	9.00	NaN	Car Maintenance	f	\N	\N	\N	\N	\N	\N	\N
1338	2025-12-19 00:00:00	citi	RESTAURANT ELBA I SANTA ANA SONMX	58.92	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1396	2025-12-23 00:00:00	chase	Zelle Payment From Jose Soto Bacwiknemxab	NaN	1960.00	Real State	f	\N	3	\N	\N	\N	\N	\N
1414	2026-01-12 00:00:00	chase	Zelle Payment From Allan C Sanceau Usbfypbrxdsn	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
1410	2026-01-05 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0Wb2D994 Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1339	2025-12-19 00:00:00	citi	EMPIRE 8145 TUCSON AZ	10.83	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1340	2025-12-20 00:00:00	citi	FLEXI DILA ZAP HERMOSILLO SOMX	83.36	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1341	2025-12-20 00:00:00	citi	MERPAGO*NEVERIAPARQUE CIUDAD DE MEXMX	14.35	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1342	2025-12-20 00:00:00	citi	REYES HERMOSILLO SOMX	8.51	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1343	2025-12-21 00:00:00	citi	SAMS BLVD MORELOS HERMOSILLO SOMX	18.32	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1344	2025-12-22 00:00:00	citi	MERPAGO*NEVERIAPARQUE CIUDAD DE MEXMX	28.02	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1345	2025-12-22 00:00:00	citi	OXXO FIRENZE HMO HERMOSILLO SOMX	6.02	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1346	2025-12-23 00:00:00	citi	MERPAGO*LAPURAVIDA CIUDAD DE MEXMX	23.12	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1347	2025-12-24 00:00:00	citi	SAL KATS HERMOSILLO SOMX	27.11	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1348	2025-12-24 00:00:00	citi	7 ELEVEN T2143 HERMOSILLO SOMX	2.24	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1349	2025-12-24 00:00:00	citi	FS PAY-HOA ASSESSMENTS FRONTSTEPS.COCO	103.95	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1350	2025-12-24 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	85.57	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1776	2026-03-13 00:00:00	citi	FAR GUAD 1563 JUAREZ CHIH MX	10.89	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1777	2026-03-13 00:00:00	citi	OXXOJANOS CJS JANOS CHIH MX	13.11	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1778	2026-03-13 00:00:00	citi	FAR GUAD 1563 JUAREZ CHIH MX	19.19	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1780	2026-03-14 00:00:00	citi	CIRCLE K # 41657 TUCSON AZ	50.69	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1781	2026-03-14 00:00:00	citi	PAGANDO*LITTLE CAESAR1 Chihuahua MX	10.65	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1782	2026-03-14 00:00:00	citi	SUPERCENTER PZA MONUME CD JUAREZ CHIMX	8.29	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1425	2025-12-22 00:00:00	banamex	PAGO INTERBANCARIO A BBVA MEXICO AL BENEF. MARIELA,ARVAYO/PELUQUERA (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 004152314004781350 CLAVE RASTREO 085904265864335455 REF. 0201225 corte pelo MISMO DIA	21.62	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1454	2026-01-14 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	11.30	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1456	2026-01-14 00:00:00	citi	RAY READY MIX 520-209-2414 AZ	882.39	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1457	2026-01-14 00:00:00	citi	FLOOR AND DECOR 141 TUCSON AZ	2955.31	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1458	2026-01-14 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	45.23	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1459	2026-01-15 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	49.94	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1460	2026-01-15 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	39.10	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1461	2026-01-15 00:00:00	citi	SQ *WATER MART #18 Tucson AZ	15.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1462	2026-01-15 00:00:00	citi	PROGRESSIVE INS 800-776-4737 OH	595.00	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1463	2026-01-15 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	5.42	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1505	2026-01-27 00:00:00	citi	ACE HDWE TUCSON AZ	10.86	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1506	2026-01-27 00:00:00	citi	ACE HDWE TUCSON AZ	103.46	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1507	2026-01-27 00:00:00	citi	SP HABISTORE 152-03261217 AZ	17.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1508	2026-01-28 00:00:00	citi	SQ *TMM'S RESTORE Tucson AZ	54.40	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1509	2026-01-28 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	26.06	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1510	2026-01-29 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	15.07	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1783	2026-03-15 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1784	2026-03-15 00:00:00	citi	REST HONG FAT CD JUAREZ CHIMX	10.14	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1785	2026-03-15 00:00:00	citi	LA NUEVA MICHOACANA CD JUAREZ CHIMX	10.43	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1786	2026-03-15 00:00:00	citi	WAL MART CD JUAREZ CD JUAREZ CHIMX	27.12	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1787	2026-03-15 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	10.87	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1788	2026-03-15 00:00:00	citi	SAVERS - 1051 TUCSON AZ	6.50	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1789	2026-03-15 00:00:00	citi	MUSEO JUAN GABRIEL JUAREZ CHIH MX	45.65	NaN	Travel	f	\N	\N	\N	\N	\N	\N	\N
1790	2026-03-15 00:00:00	citi	S MART SATELITE JUAREZ CHIH MX	35.43	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1791	2026-03-16 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	36.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1476	2026-01-19 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	365.69	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1477	2026-01-19 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	24.91	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1478	2026-01-19 00:00:00	citi	TUCSON RUBBERIZED COAT TUCSON AZ	86.96	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1479	2026-01-19 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	32.77	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1480	2026-01-19 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	19.56	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1481	2026-01-19 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	NaN	19.56	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1482	2026-01-20 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	45.66	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1483	2026-01-21 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	75.46	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1484	2026-01-21 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	31.83	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1485	2026-01-21 00:00:00	citi	THE HOME DEPOT #0474 TUCSON AZ	104.47	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1511	2026-01-29 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	39.11	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1512	2026-01-29 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	116.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1513	2026-01-30 00:00:00	citi	AMAZON MKTPL*IZ7RH9JP3 Amzn.com/billWA	13.75	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1514	2026-01-30 00:00:00	citi	RAISING CANES 0598 TUCSON AZ	37.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1515	2026-01-30 00:00:00	citi	THE HOME DEPOT 467 TUCSON AZ	97.86	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1516	2026-01-30 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	9.70	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1517	2026-01-30 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	24.19	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1518	2026-01-30 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	43.31	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1519	2026-01-31 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	24.98	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1520	2026-02-01 00:00:00	citi	RAISING CANES 0598 TUCSON AZ	2.93	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1521	2026-02-01 00:00:00	citi	RAISING CANES 0598 TUCSON AZ	56.38	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1522	2026-02-02 00:00:00	citi	PAYPAL *EBAY US 786-762-515 CA	3.91	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1524	2026-02-02 00:00:00	citi	DAIRY QUEEN #15443 TUCSON AZ	23.33	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1525	2026-02-02 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	10.33	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1526	2026-02-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	3152.46	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1528	2026-02-04 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	147.26	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1529	2026-02-04 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	46.36	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1530	2026-02-04 00:00:00	citi	LOWES #01791* TUCSON AZ	53.81	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1531	2026-02-04 00:00:00	citi	PANDA EXPRESS #1837 TUCSON AZ	28.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1532	2026-02-04 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	66.07	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1533	2026-02-04 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	247.13	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1534	2026-02-04 00:00:00	citi	LOWES #01791* TUCSON AZ	NaN	177.31	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1536	2026-02-06 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	1297.24	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1537	2026-02-06 00:00:00	citi	SHERWIN-WILLIAMS727632 TUCSON AZ	127.51	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1538	2026-02-06 00:00:00	citi	SHERWIN-WILLIAMS727632 TUCSON AZ	20.61	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1539	2026-02-06 00:00:00	citi	CHIPOTLE 3043 TUCSON AZ	34.19	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1540	2026-02-06 00:00:00	citi	AMAZON RETA* 8X5YR8AZ3	108.69	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1541	2026-02-06 00:00:00	citi	SP HABISTORE 152-03261217 AZ	30.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1542	2026-02-07 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	182.05	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1543	2026-02-07 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	28.10	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1566	2026-02-02 00:00:00	chase	Nsm Dbamr.Cooper Nsm Dbamr 1286336 Web ID: 0000452701	1529.48	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1567	2026-02-02 00:00:00	chase	Zelle Payment To Kristin Manning (Dishwasher) Jpm99C497Y5D	100.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1568	2026-02-03 00:00:00	chase	Citi Autopay Payment 291925840330072 Web ID: Citicardap	3152.46	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1523	2026-02-02 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	121.64	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1570	2026-02-03 00:00:00	chase	Honda Pmt 8004451358 PPD ID: A953472715	625.43	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1571	2026-02-05 00:00:00	chase	02/05 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1572	2026-02-06 00:00:00	chase	Zelle Payment To Manuel (Pinturas) Jpm99C4Mgf82	80.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1573	2026-02-09 00:00:00	chase	Zelle Payment To Martin Pesqueira Jpm99C5074Kx	400.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1574	2026-02-13 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.09	Income	f	\N	\N	\N	\N	\N	\N	\N
1575	2026-02-13 00:00:00	chase	Remote Online Deposit 1	NaN	40.00	Income	f	\N	\N	\N	\N	\N	\N	\N
1577	2026-02-17 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1578	2026-02-05 00:00:00	banamex	PAGO INTERBANCARIO A SANTANDER AL BENEF. GRACIELA,CARDENAS/QUINTERO (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 005579070044739970 CLAVE RASTREO 085908148694303562 REF. 0040226 mandado y gastos MISMO DIA	286.49	NaN	Papas	f	\N	\N	\N	\N	\N	\N	\N
1583	2026-02-09 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	226.03	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1584	2026-02-09 00:00:00	citi	AMAZON RETA* PC32A7L93 5% on gas at Costco ............................. +$6.42	270.66	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1585	2026-02-09 00:00:00	citi	HOTELCOM73370068019844 HOTELS.COM WA	1195.60	NaN	Travel	f	\N	\N	\N	\N	\N	\N	\N
1586	2026-02-10 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	45.66	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1587	2026-02-10 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	90.63	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1588	2026-02-10 00:00:00	citi	AMAZON RETA* AP57Y5B63	37.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1589	2026-02-11 00:00:00	citi	COT ES LOS REALES SCALES TUCSON AZ	15.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1590	2026-02-11 00:00:00	citi	AMAZON MARK* YU9AL8LI3 Total Earned: $135.21	45.64	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1591	2026-02-11 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	97.26	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1592	2026-02-12 00:00:00	citi	WAL-MART #4490 TUCSON AZ	16.56	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1593	2026-02-12 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	27.87	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1594	2026-02-12 00:00:00	citi	WAL-MART #5858 TUCSON AZ	20.91	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1595	2026-02-12 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1596	2026-02-13 00:00:00	citi	MERPAGO*OCHOAS CIUDAD DE MEXMX	44.17	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1597	2026-02-13 00:00:00	citi	AMAZON MARK* PK3HZ84Z3	83.69	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1598	2026-02-13 00:00:00	citi	PAYPAL *EXPRESSSCRI 402-935-7733 MO	5.48	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1599	2026-02-13 00:00:00	citi	NETFLIX, INC. 186-65797172 CA	19.56	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
1600	2026-02-13 00:00:00	citi	FIRST WATCH 0674 PAT 941-907-9800 AZ	36.28	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1601	2026-02-13 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	8.30	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1602	2026-02-13 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	39.70	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1603	2026-02-13 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	157.53	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1604	2026-02-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	44.49	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1605	2026-02-14 00:00:00	citi	FARM YZATOSALI HERMOSILLO SOMX	43.87	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1606	2026-02-14 00:00:00	citi	NETPAY *GREASE MONKEY HERMOSILLO MX	172.64	NaN	Car Maintenance	f	\N	\N	\N	\N	\N	\N	\N
1792	2026-03-16 00:00:00	citi	ESTACION CARLOS AMAYA CD JUAREZ CHIMX	55.23	NaN	Travel	f	\N	\N	\N	\N	\N	\N	\N
1793	2026-03-16 00:00:00	citi	BURRITOSJUAREZ ALAMEDA CD JUAREZ CHIMX	15.53	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1576	2026-02-13 00:00:00	chase	Zelle Payment From Allan C Sanceau Usb2Wlgrg2Ke	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
1569	2026-02-03 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0Wp5Shww Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1795	2026-03-17 00:00:00	citi	APPLEBBEES CAMPOS ELIS CD JUAREZ CHIMX	65.14	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1798	2026-03-18 00:00:00	citi	SUBURBIA LAS MISIONES JUAREZ CHIH MX	65.66	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1799	2026-03-18 00:00:00	citi	CLIP MX*JUAREZ SHOP JUAREZ MX	91.06	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1800	2026-03-18 00:00:00	citi	FOOD CITY #171 TUCSON AZ	28.55	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1801	2026-03-19 00:00:00	citi	SUPERETTE DEL RIO JUAREZ CHIH MX	18.27	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1802	2026-03-19 00:00:00	citi	LA NUEVA MICHOACANA CD JUAREZ CHIMX	6.51	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1803	2026-03-19 00:00:00	citi	MERPAGO*TOURPORJUAREZ CIUDAD DE MEXMX	26.62	NaN	Travel	f	\N	\N	\N	\N	\N	\N	\N
1804	2026-03-19 00:00:00	citi	EL MANDIL SONORENSE CD JUAREZ CHIMX	20.09	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1805	2026-03-19 00:00:00	citi	PANDA EXPRESS #1837 TUCSON AZ	15.11	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1806	2026-03-20 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	29.75	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1807	2026-03-20 00:00:00	citi	ROSS STORES #999 TUCSON AZ	86.90	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1808	2026-03-20 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	17.60	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1809	2026-03-20 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	19.54	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1810	2026-03-20 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	NaN	23.90	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1811	2026-03-20 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	NaN	29.33	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1579	2026-02-08 00:00:00	citi	QT 1470 TUCSON AZ	11.28	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1607	2026-02-14 00:00:00	citi	GASERV MORELOS HERMOSILLO SOMX	63.29	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1608	2026-02-14 00:00:00	citi	PANIFICADORA Y PASTELE HERMOSILLO SOMX	19.73	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1609	2026-02-14 00:00:00	citi	REST PAPA FRIJOL HERMOSILLO SOMX	69.23	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1611	2026-02-14 00:00:00	citi	AMAZON MARK* YJ7RS3UK3	21.72	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1612	2026-02-15 00:00:00	citi	FONDA EL JAVIAN URES SON MX	37.95	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1613	2026-02-15 00:00:00	citi	SUPER PAZ MART URES SON MX	57.10	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1614	2026-02-15 00:00:00	citi	CLIP MX*5 RIOS RESTAUR URES MX	19.03	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1615	2026-02-15 00:00:00	citi	MCDONALD'S F3811 NOGALES AZ	12.13	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1616	2026-02-15 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	14.13	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1617	2026-02-16 00:00:00	citi	TOMMYS EXPRESS AZ452 161-63698917 AZ	9.00	NaN	Car Maintenance	f	\N	\N	\N	\N	\N	\N	\N
1618	2026-02-16 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	31.34	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1619	2026-02-16 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	47.07	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1623	2026-02-18 00:00:00	citi	ROSS STORES #544 TUCSON AZ	65.20	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1624	2026-02-18 00:00:00	citi	BURLINGTON STORES 1250 TUCSON AZ	65.20	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1625	2026-02-19 00:00:00	citi	SP HABISTORE 152-03261217 AZ	5.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1626	2026-02-19 00:00:00	citi	THE HOME DEPOT #0474 TUCSON AZ	404.38	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1627	2026-02-20 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	21.72	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1628	2026-02-20 00:00:00	citi	LITTLE CAESARS #3168 800-722-3727 AZ	20.63	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1629	2026-02-21 00:00:00	citi	COT ES LOS REALES SCALES TUCSON AZ	15.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1630	2026-02-21 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	310.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1796	2026-03-17 00:00:00	citi	HOTEL CONQUISTADOR CD JUAREZ CHIMX	391.03	NaN	Papas	t	Green Card Papas	\N	\N	\N	\N	\N	\N
1797	2026-03-18 00:00:00	citi	FACEBK *87N6PGVYX2 650-5434800 DE	5.64	NaN	Real State	t	Kostka Rent Advertisement	\N	\N	\N	\N	\N	\N
1813	2026-03-20 00:00:00	citi	HOTEL FRONTERA INN AGUA PRIETA SMX	66.78	NaN	Papas	t	Green Card Papas	\N	\N	\N	\N	\N	\N
1814	2026-03-20 00:00:00	citi	OXXO EJERCITO NAC CD JUAREZ CHIMX	1.41	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1815	2026-03-20 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	1.78	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1816	2026-03-21 00:00:00	citi	WINGSTOP 0088 TUCSON AZ	56.60	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1636	2026-02-23 00:00:00	citi	MARISCOS CHIHUAHUA TUCSON AZ	100.46	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1637	2026-02-23 00:00:00	citi	EL SUPER # 10 TUCSON AZ	44.30	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1638	2026-02-23 00:00:00	citi	AMAZON MARK* B95KV0F01	5.79	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1639	2026-02-24 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	141.28	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1684	2026-03-04 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	100.98	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1685	2026-03-04 00:00:00	citi	BURLINGTON STORES 1250 TUCSON AZ	28.23	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1686	2026-03-04 00:00:00	citi	BURLINGTON STORES 1250 TUCSON AZ	NaN	65.20	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1687	2026-03-05 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	11.63	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1733	2026-03-02 00:00:00	chase	Rocket Mortgage Loan 0995739 Web ID: 0000452701	1529.48	NaN	Utilities	t	\N	\N	\N	\N	\N	\N	\N
1688	2026-03-05 00:00:00	citi	YOLOPAY*VENDING MONTERREY NL MX	0.46	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1690	2026-03-05 00:00:00	citi	SUBWAY 54164 SANTA ANA SONMX	29.68	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1691	2026-03-05 00:00:00	citi	REST ASIAN EXPRESS S J SANTA ANA SONMX	9.65	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1692	2026-03-05 00:00:00	citi	YOLOPAY*VENDING MONTERREY NL MX	1.20	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1693	2026-03-05 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	30.39	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1694	2026-03-05 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	124.41	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1697	2026-03-05 00:00:00	citi	CIRCLE K # 03443 NOGALES AZ	27.14	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1698	2026-03-05 00:00:00	citi	WM SUPERCENTER #5626 TUCSON AZ	19.96	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1699	2026-03-05 00:00:00	citi	YOLOPAY*VENDING MONTERREY NL MX	1.71	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1620	2026-02-18 00:00:00	citi	AMAZON MKTPLACE PMTS Amzn.com/billWA	NaN	13.75	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1621	2026-02-18 00:00:00	citi	AMAZON MKTPLACE PMTS Amzn.com/billWA	NaN	15.48	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1702	2026-03-06 00:00:00	citi	FARM JOSE MANUEL ROBLE HERMOSILLO SOMX	20.46	NaN	Pharmacy/Health	f	\N	3	\N	\N	\N	\N	\N
1683	2026-03-04 00:00:00	citi	AMAZON PRIME*QF0ZI52Y3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1703	2026-03-06 00:00:00	citi	MERPAGO*TACARBON CIUDAD DE MEXMX	29.46	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1704	2026-03-06 00:00:00	citi	BOL SATELITE HERMOSILLO SOMX	67.18	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1700	2026-03-06 00:00:00	citi	BOL SATELITE HERMOSILLO SOMX	21.55	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1706	2026-03-07 00:00:00	citi	CASA GARMENDIA HERMOSILLO SOMX	111.67	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1707	2026-03-07 00:00:00	citi	REYES HERMOSILLO SOMX	3.40	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1708	2026-03-07 00:00:00	citi	MERPAGO*TWENTYSHOP CIUDAD DE MEXMX	10.72	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1725	2026-02-25 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1795.51	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1726	2026-02-26 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	80.65	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1727	2026-02-27 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1728	2026-02-27 00:00:00	chase	Zelle Payment To Erick Gonzales Jpm99C746Tbr	55.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1701	2026-03-06 00:00:00	citi	BIO PLASMA HERMOSILLO SOMX	227.97	NaN	Pharmacy/Health	f	Votox Reyna	\N	\N	\N	\N	\N	\N
1729	2026-02-27 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
1730	2026-03-02 00:00:00	chase	Costco Cash Reward PPD ID: Costcorewd	NaN	958.55	Income	f	\N	\N	\N	\N	\N	\N	\N
1732	2026-03-02 00:00:00	chase	Zelle Payment To Reyna Maria 27905529338	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
1734	2026-03-02 00:00:00	chase	Xoom Debit OID 38537966 Web ID: 1770510487	603.69	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1735	2026-03-03 00:00:00	chase	Citi Autopay Payment 291950037440012 Web ID: Citicardap	15302.11	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1737	2026-03-03 00:00:00	chase	Honda Pmt 8004451358 PPD ID: A953472715	625.43	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1739	2026-03-05 00:00:00	chase	Zelle Payment From Yesenia Valenzuela 28314638769	NaN	1325.00	Real State	f	\N	\N	\N	\N	\N	\N	\N
1740	2026-03-05 00:00:00	chase	03/05 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1743	2026-03-13 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
1745	2026-03-17 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1746	2026-03-02 00:00:00	banamex	PAGO INTERBANCARIO A SANTANDER AL BENEF. GRACIELA,CARDENAS/QUINTERO (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 005579070044739970 CLAVE RASTREO 085904984234306062 REF. 0010326 mandado y gastos MISMO DIA	286.49	NaN	Papas	f	\N	\N	\N	\N	\N	\N	\N
1817	2026-03-21 00:00:00	citi	DILA GUAYMAS HERMOSILLO SOMX	8.99	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1818	2026-03-21 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	8.09	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1696	2026-03-05 00:00:00	citi	FACEBK *7T69TH5AP2 650-5434800 DE	2.00	NaN	Real State	t	Kostka Advertisement	4	\N	\N	\N	\N	\N
1741	2026-03-05 00:00:00	chase	Zelle Payment From Valdez Concrete LLC Bacmfpdyjf4S	NaN	1850.00	Real State	t	Kostka Rent Deposit	4	\N	\N	\N	\N	\N
1695	2026-03-05 00:00:00	citi	FACEBK *A2PVKHH9P2 650-5434800 DE	2.24	NaN	Real State	t	Kostka Advertisement	4	\N	\N	\N	\N	\N
1738	2026-03-04 00:00:00	chase	Remote Online Deposit 1	NaN	200.00	Real State	t	Kostka Closing Cost Refund, i.e. notary expense	4	\N	\N	\N	\N	\N
1731	2026-03-02 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	50.27	NaN	Pharmacy/Health	t	Membership Renewal	\N	\N	\N	\N	\N	\N
1748	2026-03-09 00:00:00	citi	CLIP MX*ASADERO EL MOI URES MX	28.22	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1749	2026-03-10 00:00:00	citi	SUPER PAZ MART URES SON MX	8.75	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1750	2026-03-10 00:00:00	citi	SUPER PAZ MART URES SON MX	19.05	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1751	2026-03-10 00:00:00	citi	LA TDA SUPER MERCAD URES SON MX	3.90	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1752	2026-03-10 00:00:00	citi	SUPER PAZ MART URES SON MX	32.43	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1753	2026-03-11 00:00:00	citi	SUPER PAZ MART URES SON MX	17.26	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1754	2026-03-11 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	6.91	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1755	2026-03-11 00:00:00	citi	LAS OFERTAS DE ARAM URES MX	29.01	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1756	2026-03-11 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	105.24	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1819	2026-03-21 00:00:00	citi	CITY SALADS MORELOS HERMOSILLO SOMX	17.19	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1821	2026-03-21 00:00:00	citi	GAS GOSOLINERO TRES M AGUA PRIETA SMX	38.06	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1822	2026-03-21 00:00:00	citi	TAQUERIA SARAHI IMURIS SON MX	20.35	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1823	2026-03-21 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	44.96	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1351	2025-12-25 00:00:00	citi	REYES HERMOSILLO SOMX	16.35	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1352	2025-12-26 00:00:00	citi	GASERV MORELOS HERMOSILLO SOMX	19.24	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1353	2025-12-26 00:00:00	citi	ESTET DON JUAN CARDENA HERMOSILLO SOMX	9.28	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1354	2025-12-26 00:00:00	citi	ABTS URL COMESTIBLES M HERMOSILLO SOMX	5.52	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1355	2025-12-26 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	15.32	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1356	2025-12-26 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	1.71	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1357	2025-12-27 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	4.87	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1358	2025-12-27 00:00:00	citi	TELCEL R2ACT CREDCHE CIUDAD DE MEXMX	0.06	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1359	2025-12-27 00:00:00	citi	FERRO MATERIALES ESTRE URES SON MX	3.92	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1709	2026-03-07 00:00:00	citi	MERPAGO*NOVEDAPICHAR CIUDAD DE MEXMX	8.51	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1710	2026-03-07 00:00:00	citi	MERPAGO*HIDALGOSCAFE CIUDAD DE MEXMX	4.54	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1711	2026-03-07 00:00:00	citi	SAL KATS HERMOSILLO SOMX	11.91	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1712	2026-03-07 00:00:00	citi	MERPAGO*CHUERRERIA CIUDAD DE MEXMX	6.31	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1713	2026-03-07 00:00:00	citi	MERPAGO*IMEXYACCESORIO CIUDAD DE	7.37	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1714	2026-03-07 00:00:00	citi	MERPAGO*DONVI CIUDAD DE MEXMX	7.94	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1742	2026-03-13 00:00:00	chase	Zelle Payment From Allan C Sanceau Usbcqabrodon	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
1744	2026-03-16 00:00:00	chase	Zelle Payment From Joaquin Samaniego 28429797240	NaN	65.00	Transfers	t	Pima County Fair	\N	\N	\N	\N	\N	\N
1715	2026-03-07 00:00:00	citi	NALLELY SOBERANES PELU HERMOSILLO SOMX	2.84	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1716	2026-03-08 00:00:00	citi	MERPAGO*LOMASANMIGUEL CIUDAD DE	49.88	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1717	2026-03-08 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	55.03	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1718	2026-03-02 00:00:00	wellsfargo	Bank of America Mortgage M07104950826 Salas M	816.94	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1719	2026-03-03 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1721	2026-03-06 00:00:00	wellsfargo	ATT Payment 030526 577172003Epayv Manuel Salas	152.01	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1722	2026-02-20 00:00:00	chase	Zelle Payment To Martin Pesqueira Jpm99C6Fsvbv	1600.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1723	2026-02-20 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	150.34	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1724	2026-02-25 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1377.75	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1747	2026-03-02 00:00:00	banamex	PAGO RECIBIDO DE TESORED POR ORDEN DE MANUEL SALAS REF.3586532 43046403606 RASTREO:	NaN	553.62	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1825	2026-03-22 00:00:00	citi	DAIRY QUEEN #15909 TUCSON AZ	8.34	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1827	2026-03-22 00:00:00	citi	SAVERS - 1051 TUCSON AZ	29.73	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1820	2026-03-21 00:00:00	citi	AUTOZONE 7079 HERMOSILLO SOMX	37.20	NaN	Car Maintenance	f	Antifreeze Aveo	\N	\N	\N	\N	\N	\N
1812	2026-03-20 00:00:00	citi	PAGANDO*BIP GASOLINE Juarez MX	28.08	NaN	Papas	t	Green Card Papas	\N	\N	\N	\N	\N	\N
1720	2026-03-03 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 64273326 Manuel Salas	34.90	NaN	Real State	t	Franklin Community	2	\N	\N	\N	\N	\N
1360	2025-12-27 00:00:00	citi	FERRO MATERIALES ESTRE URES SON MX	11.47	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1757	2026-03-11 00:00:00	citi	PAPELERIA ALE HERMOSILLO SOMX	1.12	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1828	2026-03-23 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	92.09	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1829	2026-03-23 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	54.16	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1830	2026-03-23 00:00:00	citi	SAVERS - 1051 TUCSON AZ	27.22	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1832	2026-03-23 00:00:00	citi	BJS RESTAURANTS 501 TUCSON AZ	81.87	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1833	2026-03-24 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	41.69	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1834	2026-03-24 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	4.99	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1835	2026-03-24 00:00:00	citi	PANDA EXPRESS #628 TUCSON AZ	33.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1836	2026-03-24 00:00:00	citi	EL SUPER # 10 TUCSON AZ	74.78	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1837	2026-03-25 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	68.04	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1839	2026-03-25 00:00:00	citi	CARNICERIA EL HERRADERO TUCSON AZ	1.29	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1885	2026-04-02 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1888	2026-04-06 00:00:00	wellsfargo	Empire Vista Assn Dues 65575181 Manuel Salas	108.00	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1889	2026-04-07 00:00:00	wellsfargo	ATT Payment 040526 790834001Epaya Manuel Salas	152.03	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1891	2026-03-20 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	111.90	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1892	2026-03-20 00:00:00	chase	Southwest Gas Payment B26078105609376 Web ID: 4880085720	69.70	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1893	2026-03-23 00:00:00	chase	Xoom Debit OID 38837745 Web ID: 1770510487	603.69	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1921	2026-04-10 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
1927	2026-04-16 00:00:00	chase	Zelle Payment From Reyna Maria Varela Souffle 28857411431	NaN	75.00	Transfers	t	\N	\N	\N	\N	\N	\N	\N
1928	2026-04-16 00:00:00	chase	Zelle Payment From Reyna Maria Varela Souffle 28857397045	NaN	240.00	Transfers	t	\N	\N	\N	\N	\N	\N	\N
1929	2026-04-16 00:00:00	chase	Zelle Payment To Highplanes Arena Jpm99Cdbbtrt	75.00	NaN	Pharmacy/Health	f	Curso de Equitacion Eleonor y Enrique juntos por 30 minutos	\N	\N	\N	\N	\N	\N
1926	2026-04-15 00:00:00	chase	Zelle Payment From Dba Liliana Ocano Hair Dresser Bacvezzqynpv	NaN	3700.00	Real State	f	\N	4	\N	\N	\N	\N	\N
1923	2026-04-10 00:00:00	chase	Zelle Payment To Iran Valdez Jpm99Ccoa115	1541.66	NaN	Real State	f	Return of rent deposit	4	\N	\N	\N	\N	\N
1922	2026-04-10 00:00:00	chase	Intuit Inc Acctverify PPD ID: 9215986206	0.18	NaN	Digital Subscriptions	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1919	2026-04-09 00:00:00	chase	Real Time Transfer Recd From Aba/Contr Bnk-021000021 From: Acctverify Intuit Inc. Ref:	NaN	0.08	Digital Subscriptions	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1887	2026-04-02 00:00:00	wellsfargo	Bank of America Mortgage 260401 P46806414 , Salas M	816.94	NaN	Real State	f	\N	1	\N	\N	\N	\N	\N
1886	2026-04-02 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 65185992 Manuel Salas	34.90	NaN	Real State	f	\N	2	\N	\N	\N	\N	\N
1894	2026-03-23 00:00:00	chase	Zelle Payment From Iran Valdez Bacs7Ufltdcx	NaN	496.00	Home Improvement	t	Kostka sewer clog repair	4	\N	\N	\N	\N	\N
1831	2026-03-23 00:00:00	citi	LAURA PILATES HERMOSILLO MX	34.72	NaN	Pharmacy/Health	t	\N	\N	\N	\N	\N	\N	\N
1361	2025-12-28 00:00:00	citi	TCONE*ABTS LA CURVA CUNDUACAN TABMX	8.39	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1362	2025-12-28 00:00:00	citi	SUPER PAZ MART URES SON MX	29.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1363	2025-12-29 00:00:00	citi	FERRO MATERIALES II URES SON MX	11.19	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1364	2025-12-30 00:00:00	citi	SUPER PAZ MART URES SON MX	133.62	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1365	2026-01-02 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	9.29	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1366	2026-01-02 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	32.27	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1826	2026-03-22 00:00:00	citi	SPROUTS FARMERS MAR TUCSON AZ	16.41	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1924	2026-04-13 00:00:00	chase	Zelle Payment From Allan C Sanceau Usbmrhvrx2Ck	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
1890	2026-03-18 00:00:00	chase	Zelle Payment From Jose Soto Bacsetj1Qp2N	NaN	2070.00	Real State	f	\N	3	\N	\N	\N	\N	\N
1367	2026-01-02 00:00:00	citi	PSM PROSEPAGO HERMOSILLO SOMX	20.62	NaN	Travel	f	\N	\N	\N	\N	\N	\N	\N
1368	2026-01-03 00:00:00	citi	SUPER PAZ MART URES SON MX	73.77	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1369	2026-01-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	5235.61	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1370	2026-01-03 00:00:00	citi	MERPAGO*CACHORIADAS CIUDAD DE MEXMX	47.41	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1371	2026-01-03 00:00:00	citi	TCONE*ABTS LA CURVA CUNDUACAN TABMX	19.31	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1372	2026-01-03 00:00:00	citi	SUPER PAZ MART URES SON MX	18.29	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1373	2026-01-04 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	11.53	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1375	2026-01-04 00:00:00	citi	WINGSTOP 0088 TUCSON AZ	40.84	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1376	2026-01-04 00:00:00	citi	SUPER PAZ MART URES SON MX	5.82	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1377	2026-01-04 00:00:00	citi	SUBWAY 54164 SANTA ANA SONMX	26.20	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1379	2026-01-05 00:00:00	citi	TOMMYS EXPRESS AZ452 161-63698917 AZ	9.00	NaN	Car Maintenance	f	\N	\N	\N	\N	\N	\N	\N
1380	2026-01-05 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	19.90	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1381	2026-01-06 00:00:00	citi	TST*LA ESTRELLA BAKERY - Tucson AZ	50.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1925	2026-04-13 00:00:00	chase	Remote Online Deposit 1	NaN	3700.00	Real State	t	\N	4	\N	\N	\N	\N	\N
1382	2026-01-06 00:00:00	citi	TUCSON RUBBERIZED COAT TUCSON AZ	110.87	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1383	2026-01-06 00:00:00	citi	QT 1490 TUCSON AZ	41.81	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1384	2026-01-06 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	54.09	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1385	2026-01-07 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	22.52	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1386	2026-01-02 00:00:00	wellsfargo	Bank of America Mortgage 260102 P44346218 , Salas M	795.34	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1387	2026-01-05 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1388	2026-01-05 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 62167808 Manuel Salas	34.90	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1389	2026-01-06 00:00:00	wellsfargo	ATT Payment 010526 477581003Epayo Manuel Salas	152.13	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1390	2026-01-06 00:00:00	wellsfargo	Empire Vista Assn Dues 62582538 Manuel Salas	108.00	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1391	2025-12-17 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1932	2026-03-23 00:00:00	banamex	PAGO RECIBIDO DE TESORED POR ORDEN DE MANUEL SALAS REF.3901067 43042038406 RASTREO:	NaN	574.92	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1903	2026-04-01 00:00:00	chase	Zelle Payment To Reyna Maria 28258354338	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
1906	2026-04-02 00:00:00	chase	Honda Pmt 8004451358 PPD ID: A953472715	625.43	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1905	2026-04-02 00:00:00	chase	Rocket Mortgage Loan 1642544 Web ID: 0000452701	1529.48	NaN	Utilities	t	\N	\N	\N	\N	\N	\N	\N
1902	2026-04-01 00:00:00	chase	Zelle Payment To Highplanes Arena Jpm99Cbc1O7U	75.00	NaN	Pharmacy/Health	f	Curso de Equitacion Eleonor y Enrique juntos por 30 minutos	\N	\N	\N	\N	\N	\N
1291	2025-12-08 00:00:00	citi	SAVERS - 1051 TUCSON AZ	23.02	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1292	2025-12-08 00:00:00	citi	AMAZON MKTPL*BI63G9990 Amzn.com/billWA	10.86	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1293	2025-12-10 00:00:00	citi	MCDONALD'S F32883 TUCSON AZ	10.87	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1294	2025-12-10 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	36.52	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1295	2025-12-10 00:00:00	citi	LITTLE CAESARS #3168 800-722-3727 AZ	9.77	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1296	2025-12-10 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	115.74	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1297	2025-12-11 00:00:00	citi	AMC 2698 FOOTHILLS 15 TUCSON AZ	10.91	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1298	2025-12-11 00:00:00	citi	AMC 2698 FOOTHILLS 15 TUCSON AZ	98.18	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1299	2025-12-11 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	40.18	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1300	2025-12-12 00:00:00	citi	WAL-MART #1612 TUCSON AZ	63.88	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1301	2025-12-12 00:00:00	citi	JCPENNEY 2913 TUCSON AZ	NaN	21.73	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1302	2025-12-12 00:00:00	citi	CARNITAS LA YOCA LLC TUCSON AZ	3.36	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1303	2025-12-12 00:00:00	citi	CARNITAS LA YOCA LLC TUCSON AZ	16.82	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1304	2025-12-12 00:00:00	citi	WAL-MART #1612 TUCSON AZ	4.42	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1305	2025-12-12 00:00:00	citi	DD'S DISCOUNTS #5422 TUCSON AZ	10.86	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1306	2025-12-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	110.84	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1307	2025-12-13 00:00:00	citi	WAL-MART #2922 TUCSON AZ	34.87	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1308	2025-12-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	26.88	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1309	2025-12-13 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	35.31	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1311	2025-12-13 00:00:00	citi	OLIVE GARDEN ZK 0021219 TUCSON AZ	53.71	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1312	2025-12-13 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1313	2025-12-13 00:00:00	citi	THE HOME DEPOT 467 TUCSON AZ	225.54	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1314	2025-12-14 00:00:00	citi	MCDONALD'S F18787 TUCSON AZ	5.44	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1315	2025-12-14 00:00:00	citi	SHELL OIL 10006175011 TUCSON AZ	20.08	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1317	2025-12-14 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	30.40	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1318	2025-12-14 00:00:00	citi	FIVE GUYS AZ 1226 QSR TUCSON AZ	50.48	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1374	2026-01-04 00:00:00	citi	WAL-MART #3049 TUCSON AZ	69.20	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1464	2026-01-16 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	153.84	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1465	2026-01-16 00:00:00	citi	FLOOR AND DECOR 141 TUCSON AZ	90.20	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1466	2026-01-16 00:00:00	citi	SP HABISTORE 152-03261217 AZ	50.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1467	2026-01-17 00:00:00	citi	AMAZON MKTPL*YF2242QP3 Amzn.com/billWA	250.31	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1378	2026-01-04 00:00:00	citi	AMAZON PRIME*2N8V56ZV3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1904	2026-04-02 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0Xh7Hp8M Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1468	2026-01-17 00:00:00	citi	TUCSON RUBBERIZED COAT TUCSON AZ	240.23	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1469	2026-01-17 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	10.87	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1470	2026-01-17 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	17.56	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1471	2026-01-18 00:00:00	citi	WAL-MART #4490 TUCSON AZ	89.95	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1472	2026-01-18 00:00:00	citi	DAIRY QUEEN #17170 TUCSON AZ	14.95	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1473	2026-01-18 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	13.75	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1474	2026-01-18 00:00:00	citi	THE GIRLS ESTATE SALES TUCSON AZ	6.52	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1475	2026-01-18 00:00:00	citi	THE HOME DEPOT #0410 TUCSON AZ	50.47	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1486	2026-01-22 00:00:00	citi	WAL-MART #4490 TUCSON AZ	3.98	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1487	2026-01-22 00:00:00	citi	WAL-MART #4490 TUCSON AZ	117.26	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1488	2026-01-22 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	43.35	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1489	2026-01-23 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	25.45	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1490	2026-01-23 00:00:00	citi	LITTLE CAESARS #3164 800-722-3727 AZ	56.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1491	2026-01-23 00:00:00	citi	THE HOME DEPOT 467 TUCSON AZ	82.61	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1492	2026-01-23 00:00:00	citi	THE HOME DEPOT 0474 TUCSON AZ	774.63	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1493	2026-01-23 00:00:00	citi	IND METAL SUPPL-TUCSON TUCSON AZ	35.30	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1494	2026-01-24 00:00:00	citi	FS PAY-HOA ASSESSMENTS FRONTSTEPS.COCO	103.95	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1495	2026-01-24 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	14.25	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1496	2026-01-24 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	12.13	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1497	2026-01-24 00:00:00	citi	LOWES #01791* TUCSON AZ	281.03	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1498	2026-01-25 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	20.01	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1622	2026-02-18 00:00:00	citi	AMAZON RETA* IX3O74JM3	31.40	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1865	2026-04-01 00:00:00	citi	SALAD AND GO #1140 TUCSON AZ	10.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1445	2026-01-12 00:00:00	citi	THE HOME DEPOT 467 TUCSON AZ	96.19	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1446	2026-01-12 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	82.02	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1428	2026-01-02 00:00:00	banamex	PAGO INTERBANCARIO A SANTANDER AL BENEF. GRACIELA,CARDENAS/QUINTERO (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 005579070044739970 CLAVE RASTREO 085903193474300167 REF. 0010126 comida y gastos feliz a o MISMO DIA	286.49	NaN	Papas	f	\N	\N	\N	\N	\N	\N	\N
1429	2026-01-07 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	5.88	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1430	2026-01-08 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	1295.02	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1431	2026-01-09 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	556.60	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1432	2026-01-09 00:00:00	citi	FIVE GUYS AZ 1667 QSR TUCSON AZ	50.48	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1433	2026-01-09 00:00:00	citi	THE HOME DEPOT #0410 TUCSON AZ	72.07	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1434	2026-01-09 00:00:00	citi	SPEEDWAY 46261 TUCSON AZ	46.05	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1435	2026-01-10 00:00:00	citi	SP HABISTORE 152-03261217 AZ	50.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1436	2026-01-10 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	52.15	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1437	2026-01-10 00:00:00	citi	TUCSON RUBBERIZED COAT TUCSON AZ	826.12	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1438	2026-01-10 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	834.76	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1439	2026-01-10 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	20.19	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1440	2026-01-11 00:00:00	citi	LITTLE CAESARS #3168 TUCSON AZ	3.47	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1441	2026-01-11 00:00:00	citi	LITTLE CAESARS #3168 800-722-3727 AZ	37.46	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1442	2026-01-11 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	3.85	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1443	2026-01-11 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	2.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1444	2026-01-11 00:00:00	citi	THE HOME DEPOT #0486 TUCSON AZ	172.67	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1447	2026-01-12 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1448	2026-01-12 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	109.44	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1450	2026-01-13 00:00:00	citi	WAL-MART #4490 TUCSON AZ	90.73	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1499	2026-01-25 00:00:00	citi	WINGSTOP 1199 TUCSON AZ	56.77	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1500	2026-01-26 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	250.78	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1501	2026-01-26 00:00:00	citi	AMAZON MKTPL*SB8P561W3 Amzn.com/billWA	25.39	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1502	2026-01-26 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	11.91	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1503	2026-01-27 00:00:00	citi	WAL-MART #4490 TUCSON AZ	69.40	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1504	2026-01-27 00:00:00	citi	SQ *TMM'S RESTORE Tucson AZ	144.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1535	2026-02-06 00:00:00	citi	AMAZON MARK* 070GG2OO3	185.87	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1631	2026-02-22 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	17.16	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1632	2026-02-22 00:00:00	citi	THE HOME DEPOT #0486 TUCSON AZ	159.50	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1633	2026-02-23 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	53.61	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1634	2026-02-23 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	664.75	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1635	2026-02-23 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	36.23	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1640	2026-02-24 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	50.96	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1641	2026-02-24 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	109.71	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1642	2026-02-24 00:00:00	citi	BONANZA DEALS & DISCOUNT TUCSON AZ	20.28	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1643	2026-02-24 00:00:00	citi	COT ES LOS REALES SCALES TUCSON AZ	15.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1644	2026-02-25 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	39.58	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1645	2026-02-25 00:00:00	citi	EL TACO SON TUCSON AZ	51.35	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1646	2026-02-25 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	613.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1647	2026-02-25 00:00:00	citi	FOOD CITY #171 TUCSON AZ	3.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1648	2026-02-25 00:00:00	citi	SQ *TMM'S RESTORE Tucson AZ	4.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1652	2026-02-26 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	49.63	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1665	2026-03-01 00:00:00	citi	SQ *CABALLERO ENTERTAINMETucson AZ	52.00	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1666	2026-03-01 00:00:00	citi	SQ *CABALLERO LLC Tucson AZ	6.00	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1580	2026-02-08 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	29.81	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1581	2026-02-08 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	361.75	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1667	2026-03-01 00:00:00	citi	SQ *CABALLERO ENTERTAINMETucson AZ	16.00	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
1668	2026-03-01 00:00:00	citi	Costco Annual Membership Renewal	141.31	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1669	2026-03-01 00:00:00	citi	CHIPOTLE 3043 TUCSON AZ	48.97	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1670	2026-03-02 00:00:00	citi	WAL-MART #4490 TUCSON AZ	46.08	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1671	2026-03-02 00:00:00	citi	FACEBK *AQQA9GMYX2 650-5434800 DE	11.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1672	2026-03-02 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	23.90	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1673	2026-03-02 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	5.92	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1674	2026-03-03 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	4.33	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1675	2026-03-03 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	1.72	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1676	2026-03-03 00:00:00	citi	ROSS STORES #1971 TUCSON AZ	38.02	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1677	2026-03-03 00:00:00	citi	T.J. MAXX #1465 TUCSON AZ	30.75	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1544	2026-02-07 00:00:00	citi	AMAZON MARK* PC2S257D3	10.86	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1545	2026-02-07 00:00:00	citi	EL HERRADERO CARNICERIA TUCSON AZ	96.57	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1546	2026-02-07 00:00:00	citi	FRYS-FOOD-DRG #020 TUCSON AZ	51.49	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1547	2026-02-08 00:00:00	citi	WM SUPERCENTER #5626 TUCSON AZ	4.16	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1548	2026-02-08 00:00:00	citi	TST*LINS GRAND BUFFET- Tucson AZ	82.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1549	2026-02-08 00:00:00	citi	WM SUPERCENTER #5626 TUCSON AZ	47.03	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1550	2026-02-02 00:00:00	wellsfargo	Bank of America Mortgage 260202 P45499142 , Salas M	816.94	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1551	2026-02-03 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1552	2026-02-03 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 63419785 Manuel Salas	34.90	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1553	2026-02-06 00:00:00	wellsfargo	ATT Payment 020526 382535001Epayt Manuel Salas	152.13	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1556	2026-01-26 00:00:00	chase	Zelle Payment To Javier Herrera 27837973967	100.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1557	2026-01-26 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1776.31	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1558	2026-01-26 00:00:00	chase	Zelle Payment To Ruben Peralta Texturizado 27832880635	490.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1559	2026-01-27 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1560	2026-01-28 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	40.45	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1562	2026-01-30 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
1563	2026-01-30 00:00:00	chase	Zelle Payment To Francisco Herrera 27889421001	285.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1564	2026-02-02 00:00:00	chase	Zelle Payment To Efrain Carpintero 27900967255	50.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1565	2026-02-02 00:00:00	chase	Zelle Payment To Reyna Maria 27538341452	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
1678	2026-03-03 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	26.76	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1679	2026-03-03 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	34.84	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1680	2026-03-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	15302.11	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1838	2026-03-25 00:00:00	citi	AMAZING DEALZ BIN STORE TUCSON AZ	5.60	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1895	2026-03-25 00:00:00	chase	Remote Online Deposit 1	NaN	4050.00	Income	f	Sonefield Rent for 2 months in advance, i.e. next payment June 21st.	\N	\N	\N	\N	\N	\N
1900	2026-03-30 00:00:00	chase	Zelle Payment From Yesenia Valenzuela 28619531662	NaN	1325.00	Real State	f	\N	1	\N	\N	\N	\N	\N
1899	2026-03-30 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	t	\N	3	\N	\N	\N	\N	\N
1897	2026-03-26 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1377.75	NaN	Real State	f	\N	4	\N	\N	\N	\N	\N
1896	2026-03-26 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1795.51	NaN	Real State	f	\N	3	\N	\N	\N	\N	\N
1682	2026-03-04 00:00:00	citi	FACEBK *L6FXEGZ9P2 650-5434800 DE	2.00	NaN	Real State	t	Kostka Advertisement	4	\N	\N	\N	\N	\N
1582	2026-02-09 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	121.71	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1681	2026-03-03 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	NaN	21.73	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1898	2026-03-27 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
1901	2026-03-31 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	34.28	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1649	2026-02-25 00:00:00	citi	WAL-MART #4490 TUCSON AZ	23.46	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1650	2026-02-26 00:00:00	citi	Google Amazon Shoppin 650-2530000 CA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1651	2026-02-26 00:00:00	citi	AMAZON MARK* B13W63RJ0	10.86	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1653	2026-02-27 00:00:00	citi	FACEBK *Z7E5ZG9YX2 650-5434800 DE	12.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1767	2026-03-13 00:00:00	citi	RAISING CANES 0437 TUCSON AZ	0.42	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1768	2026-03-13 00:00:00	citi	COSTCO GAS #0407 TUCSON AZ	41.39	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1554	2026-01-26 00:00:00	chase	Zelle Payment From Jose Soto Baczzstoj9Hr	NaN	1940.00	Real State	f	\N	3	\N	\N	\N	\N	\N
1907	2026-04-03 00:00:00	chase	Citi Autopay Payment 291976775450147 Web ID: Citicardap	8084.21	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1910	2026-04-06 00:00:00	chase	04/06 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1920	2026-04-10 00:00:00	chase	HSA - Umb Bank HSA Cont HSA - Umb Bank Web ID: 2431357092	NaN	2096.00	Transfers	f	Error in Modular Mining W2 which made taxes raise over funding HSA account	\N	\N	\N	\N	\N	\N
1918	2026-04-09 00:00:00	chase	Real Time Transfer Recd From Aba/Contr Bnk-021000021 From: Acctverify Intuit Inc. Ref:	NaN	0.10	Digital Subscriptions	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1917	2026-04-09 00:00:00	chase	Zelle Payment To Highplanes Arena Jpm99Ccerdfp	75.00	NaN	Pharmacy/Health	f	Curso de Equitacion Eleonor y Enrique juntos por 30 minutos	\N	\N	\N	\N	\N	\N
1916	2026-04-08 00:00:00	chase	AZ Dept of Rev Tax Refund PPD ID: 1866004799	NaN	703.00	Income	f	State Tax Return for 2025	\N	\N	\N	\N	\N	\N
1654	2026-02-27 00:00:00	citi	AZIAN 520-7778311 AZ	82.58	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1655	2026-02-27 00:00:00	citi	DAIRY QUEEN #15104 TUCSON AZ	12.57	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1656	2026-02-27 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	26.30	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1657	2026-02-28 00:00:00	citi	ZILLOW *RENT LISTINGS 866-961-2570 WA	39.99	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
1658	2026-02-28 00:00:00	citi	AMAZON MARK* B928A4ER0	29.94	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1659	2026-02-28 00:00:00	citi	WINGSTOP 1199 TUCSON AZ	3.11	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1660	2026-02-28 00:00:00	citi	WINGSTOP 1199 520-888-0110 AZ	55.84	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1661	2026-02-28 00:00:00	citi	WAL-MART #5858 TUCSON AZ	3.72	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1662	2026-02-28 00:00:00	citi	WM SUPERCENTER #5858 TUCSON AZ	5.36	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1663	2026-02-28 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	20.42	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1664	2026-02-28 00:00:00	citi	THE HOME DEPOT #0474 TUCSON AZ	90.96	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1915	2026-04-07 00:00:00	chase	Olb-Verification Olb Vtrans PPD ID: 1363213132	NaN	0.01	Transfers	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1914	2026-04-07 00:00:00	chase	Olb-Verification Olb Vtrans PPD ID: 1363213132	0.01	NaN	Transfers	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1913	2026-04-07 00:00:00	chase	Olb-Verification Olb Vtrans PPD ID: 1363213132	0.28	NaN	Transfers	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1912	2026-04-07 00:00:00	chase	Olb-Verification Olb Vtrans PPD ID: 1363213132	NaN	0.28	Transfers	f	Quickbooks account transfer check	\N	\N	\N	\N	\N	\N
1909	2026-04-06 00:00:00	chase	Zelle Payment To Brianna Jpm99Cbuczps	2.50	NaN	Restaurants	t	\N	\N	\N	\N	\N	\N	\N
1908	2026-04-06 00:00:00	chase	Zelle Payment To Brianna Jpm99Cbucs7F	17.00	NaN	Restaurants	t	\N	\N	\N	\N	\N	\N	\N
1758	2026-03-12 00:00:00	citi	RESTAURANT ELBA I SANTA ANA SONMX	77.96	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1759	2026-03-12 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	68.79	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1760	2026-03-12 00:00:00	citi	MCDONALD'S F3811 NOGALES AZ	11.90	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1763	2026-03-12 00:00:00	citi	GASERV MORELOS HERMOSILLO SOMX	33.59	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1764	2026-03-13 00:00:00	citi	COSTCO WHSE #0407 TUCSON AZ	18.34	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1765	2026-03-13 00:00:00	citi	COSTCO WHSE #0407 TUCSON AZ	28.05	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1766	2026-03-13 00:00:00	citi	GOODWILL OF SO AZ HOUGHTOTUCSON AZ	6.78	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1769	2026-03-13 00:00:00	citi	RAISING CANES 0437 TUCSON AZ	23.12	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1770	2026-03-13 00:00:00	citi	ROSS STORES #85 TUCSON AZ	7.60	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1771	2026-03-13 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	11.95	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1761	2026-03-12 00:00:00	citi	HOTEL FRONTERA INN AGUA PRIETA SMX	107.42	NaN	Papas	t	Green Card Papas	\N	\N	\N	\N	\N	\N
1762	2026-03-12 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	58.86	NaN	Real State	t	\N	4	\N	\N	\N	\N	\N
1934	2026-03-30 00:00:00	banamex	PAGO INTERBANCARIO A BBVA MEXICO AL BENEF. MARIELA,ARVAYO/PELUQUERA (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 004152314004781350 CLAVE RASTREO 085903065964308767 REF. 0280326 corte pelo MISMO DIA	18.92	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1935	2026-04-06 00:00:00	banamex	PAGO INTERBANCARIO A SANTANDER AL BENEF. GRACIELA,CARDENAS/QUINTERO (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 005579070044739970 CLAVE RASTREO 085905533724309269 REF. 0020426 mandado y gastos MISMO DIA	297.30	NaN	Papas	f	\N	\N	\N	\N	\N	\N	\N
1841	2026-03-27 00:00:00	citi	WAL-MART #5626 TUCSON AZ	15.95	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1842	2026-03-27 00:00:00	citi	WM SUPERCENTER #5626 TUCSON AZ	14.74	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1843	2026-03-27 00:00:00	citi	WAL-MART #5626 TUCSON AZ	35.36	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1844	2026-03-27 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	37.98	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1847	2026-03-27 00:00:00	citi	SQ *BAJA CAFE CAMPBELL Tucson AZ	52.74	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1848	2026-03-27 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	29.17	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1849	2026-03-27 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	50.42	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1850	2026-03-28 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	49.44	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1851	2026-03-28 00:00:00	citi	NALLELY SOBERANES PELU HERMOSILLO SOMX	11.58	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1852	2026-03-28 00:00:00	citi	TCONE AGREGADOR CIUDAD DE MEXMX	4.48	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1853	2026-03-28 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	10.86	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1854	2026-03-29 00:00:00	citi	SUPER PAZ MART URES SON MX	72.06	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1855	2026-03-29 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	3.08	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1856	2026-03-29 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	11.53	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1858	2026-03-30 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	14.63	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1859	2026-03-30 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	20.04	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1860	2026-03-31 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	56.63	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1911	2026-04-06 00:00:00	chase	Zelle Payment From Jose Soto Bacyp186Jto1	NaN	829.00	Real State	f	Rent for April, remaining was paid from contract work on Kostka	3	\N	\N	\N	\N	\N
1861	2026-03-31 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	28.15	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1864	2026-04-01 00:00:00	citi	GOODWILL ARIZONA TUCSON AZ	11.97	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1857	2026-03-30 00:00:00	citi	0000000000000000000000000CIUDAD DE MEXMX	44.56	NaN	Travel	t	\N	\N	\N	\N	\N	\N	\N
1862	2026-03-31 00:00:00	citi	USPS PO 0388910739 TUCSON AZ	6.08	NaN	Real State	f	Certified mail for asking to terminate lease due to material breach	\N	\N	\N	\N	\N	\N
1846	2026-03-27 00:00:00	citi	AUTOZONE #6865 TUCSON AZ	67.32	NaN	Car Maintenance	f	Tacoma spark plug coil	\N	\N	\N	\N	\N	\N
1845	2026-03-27 00:00:00	citi	AUTOZONE #6865 TUCSON AZ	55.43	NaN	Car Maintenance	f	Tacoma spark plugs	\N	\N	\N	\N	\N	\N
1863	2026-03-31 00:00:00	citi	USCIS ELIS IV FEE 800-375-5283 DC	470.00	NaN	Travel	t	Green Card Papas	\N	\N	\N	\N	\N	\N
1872	2026-04-03 00:00:00	citi	FACEBK *GWT58L99P2 650-5434800 DE	2.75	NaN	Real State	t	\N	4	\N	\N	\N	\N	\N
1866	2026-04-01 00:00:00	citi	CHICK-FIL-A #05676 TUCSON AZ	4.33	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1867	2026-04-02 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	31.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1868	2026-04-02 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	50.02	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
1869	2026-04-02 00:00:00	citi	WINGSTOP 1199 TUCSON AZ	4.79	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1870	2026-04-02 00:00:00	citi	WINGSTOP 1199 TUCSON AZ	77.75	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1871	2026-04-02 00:00:00	citi	WWW COSTCO COM 800-955-2292 WA	103.87	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1873	2026-04-03 00:00:00	citi	DILLARDS 914 PARK PLAC TUCSON AZ	43.47	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1874	2026-04-03 00:00:00	citi	MARSHALLS #0760 TUCSON AZ	27.14	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1875	2026-04-03 00:00:00	citi	WAL-MART #4490 TUCSON AZ	10.84	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1876	2026-04-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	8084.21	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1877	2026-04-03 00:00:00	citi	LA MICHOACANA ICE CREAM TUCSON AZ	23.91	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1878	2026-04-03 00:00:00	citi	LA MICHOACANA ICE CREAM TUCSON AZ	11.96	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
1879	2026-04-04 00:00:00	citi	T.J. MAXX #1465 TUCSON AZ	68.43	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1880	2026-04-04 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	3.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
1882	2026-04-04 00:00:00	citi	INTUIT *TURBOTAX CL.INTUIT.COMCA	15.00	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
1883	2026-04-06 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	54.29	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
1884	2026-04-06 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	85.04	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5806	2026-04-07 00:00:00	citi	COT BUSINESS CENTER https://ipchaAZ	75.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5807	2026-04-08 00:00:00	citi	SQ *BIRRIERIA GUASAVE #2 Tucson AZ	46.16	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5808	2026-04-08 00:00:00	citi	SQ *BIRRIERIA GUASAVE #2 Tucson AZ	10.05	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5809	2026-04-09 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	98.56	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5810	2026-04-10 00:00:00	citi	SUPER STAR CAR WASH VALE TUCSON AZ	20.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5811	2026-04-10 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	43.79	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5812	2026-04-10 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	63.02	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5813	2026-04-10 00:00:00	citi	RAISING CANES 0598 TUCSON AZ	31.83	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5814	2026-04-10 00:00:00	citi	INTUIT *QBooks Online CL.INTUIT.COMCA	20.65	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
5815	2026-04-11 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	127.49	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5816	2026-04-11 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	47.60	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5817	2026-04-11 00:00:00	citi	DAIRY QUEEN #17787 TUCSON AZ	33.31	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5818	2026-04-12 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5819	2026-04-12 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	7.30	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5822	2026-04-13 00:00:00	citi	TST*SUSHI GARDEN - LANDI Tucson AZ	97.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5823	2026-04-13 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	24.19	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5824	2026-04-14 00:00:00	citi	PIMA COUNTY FAIR 800-514-3849 NC	29.44	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5825	2026-04-15 00:00:00	citi	RCSFUN CARNIVAL WWW.RCSFUN.COAZ	180.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5827	2026-04-15 00:00:00	citi	ROUND1 AM - PPM AZ TUCSONTUCSON AZ	21.74	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5828	2026-04-15 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	12.96	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5829	2026-04-15 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	315.67	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5830	2026-04-15 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	63.52	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5831	2026-04-16 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	7.61	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5832	2026-04-17 00:00:00	citi	ROASTED CORN PHOENIX AZ	22.97	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5833	2026-04-17 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	62.24	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5834	2026-04-17 00:00:00	citi	THECHILDRENSPLACE.COM 201-558-2683 NJ	58.69	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5835	2026-04-17 00:00:00	citi	WAL-MART #4490 TUCSON AZ	58.73	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5836	2026-04-17 00:00:00	citi	WEST COAST WEENIES 3 IRVINE CA	10.01	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5837	2026-04-17 00:00:00	citi	ROASTED CORN PHOENIX AZ	14.48	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5838	2026-04-17 00:00:00	citi	ETIX RETAIL 919-653-0544 NC	8.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5839	2026-04-17 00:00:00	citi	CHAN'S CHICKEN #2 FULSHEAR TX	16.98	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5841	2026-04-18 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	26.67	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5842	2026-04-18 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	97.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5843	2026-04-18 00:00:00	citi	FACEBK *2LBPMMDYX2 650-5434800 DE	5.81	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5844	2026-04-18 00:00:00	citi	THE HOME DEPOT 467 TUCSON AZ	271.95	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
1840	2026-03-26 00:00:00	citi	Google Amazon Shoppin 650-2530000 CA	16.29	NaN	Shopping	t	\N	\N	\N	\N	\N	\N	\N
5840	2026-04-17 00:00:00	citi	SQ *SUCK IT UP CONCESSIONJurupa ValleyCA	22.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5821	2026-04-13 00:00:00	citi	SPROUTS FARMERS MAR TUCSON AZ	10.00	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5845	2026-04-18 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	68.42	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5846	2026-04-18 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	500.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5847	2026-04-18 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	54.33	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5848	2026-04-18 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	54.33	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5849	2026-04-18 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	81.20	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5851	2026-04-18 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	66.65	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5852	2026-04-19 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	14.82	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5853	2026-04-19 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	9.59	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5854	2026-04-19 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	3.43	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5855	2026-04-19 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	30.55	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5856	2026-04-19 00:00:00	citi	PANDA EXPRESS #989 TUCSON AZ	32.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5857	2026-04-19 00:00:00	citi	EL HERRADERO CARNICERIA TUCSON AZ	8.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5858	2026-04-19 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	38.73	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5859	2026-04-19 00:00:00	citi	QT 1470 TUCSON AZ	2.55	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5860	2026-04-21 00:00:00	citi	DAIRY QUEEN #17787 TUCSON AZ	10.40	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5861	2026-04-21 00:00:00	citi	WINGSTOP 1199 TUCSON AZ	59.67	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5862	2026-04-21 00:00:00	citi	BONANZA DEALS TUCSON AZ	6.51	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5863	2026-04-21 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	29.91	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5864	2026-04-21 00:00:00	citi	SQ *WATER MART #18 Tucson AZ	9.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5865	2026-04-22 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	394.26	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5866	2026-04-22 00:00:00	citi	LAURA PILATES HERMOSILLO MX	36.03	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5867	2026-04-22 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	73.83	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5868	2026-04-22 00:00:00	citi	QT 1490 TUCSON AZ	19.80	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5869	2026-04-22 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	95.48	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5870	2026-04-23 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	125.35	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5871	2026-04-23 00:00:00	citi	THE CHILDRENS PLACE 1634 TUCSON AZ	15.21	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5872	2026-04-23 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	119.56	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5873	2026-04-23 00:00:00	citi	THE CHILDRENS PLACE 1634 TUCSON AZ	NaN	58.69	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5874	2026-04-23 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	55.39	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5875	2026-04-23 00:00:00	citi	AMAZON MKTPL*BY8059M50 Amzn.com/billWA	8.36	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5876	2026-04-24 00:00:00	citi	CARNITAS LA YOCA LLC TUCSON AZ	18.82	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5877	2026-04-24 00:00:00	citi	CARNITAS LA YOCA LLC TUCSON AZ	2.88	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5878	2026-04-24 00:00:00	citi	MCDONALD'S F5481 TUCSON AZ	4.12	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5879	2026-04-24 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	1.38	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5880	2026-04-24 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	16.25	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5881	2026-04-24 00:00:00	citi	REST ASADERO PURO PA D HERMOSILLO SOMX	16.14	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5882	2026-04-24 00:00:00	citi	REST ASADERO PURO PA D HERMOSILLO SOMX	24.20	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5883	2026-04-25 00:00:00	citi	McDonalds 43260 TUCSON AZ	29.58	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5884	2026-04-25 00:00:00	citi	MERPAGO*LAPURAVIDA HERMOSILLO MX	8.64	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5885	2026-04-25 00:00:00	citi	HERMOL GASOL HERMOSILLO SOMX	48.17	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5886	2026-04-25 00:00:00	citi	NEVERIA EL PATIO HERMOSILLO SOMX	16.48	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5887	2026-04-25 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	72.46	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5888	2026-04-26 00:00:00	citi	ABTS LA TDA URES SON MX	33.11	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5889	2026-04-26 00:00:00	citi	TCONE AGREGADOR CIUDAD DE MEXMX	5.47	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5890	2026-04-26 00:00:00	citi	Google Amazon Shoppin 650-2530000 CA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5891	2026-04-26 00:00:00	citi	KFC C750053 NOGALES AZ	36.69	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5892	2026-04-27 00:00:00	citi	WM SUPERCENTER #4603 TUCSON AZ	77.61	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5893	2026-04-27 00:00:00	citi	SAVERS - 1051 TUCSON AZ	38.08	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5894	2026-04-28 00:00:00	citi	QT 1480 OUTSIDE TUCSON AZ	73.30	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5895	2026-04-28 00:00:00	citi	T.J. MAXX #1465 TUCSON AZ	82.58	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5896	2026-04-28 00:00:00	citi	LITTLE CAESARS #3168 800-722-3727 AZ	9.77	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5897	2026-04-28 00:00:00	citi	ROSS STORES #1971 TUCSON AZ	129.79	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5898	2026-04-28 00:00:00	citi	QT 1490 TUCSON AZ	66.23	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5899	2026-04-29 00:00:00	citi	BURLINGTON STORES 754 TUCSON AZ	173.46	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5900	2026-04-30 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	134.24	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5901	2026-04-30 00:00:00	citi	WM SUPERCENTER #5626 TUCSON AZ	10.80	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5902	2026-04-30 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	2.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5903	2026-04-30 00:00:00	citi	WAL-MART #5626 TUCSON AZ	338.06	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5904	2026-05-01 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	2.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5905	2026-05-01 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	137.80	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5906	2026-05-01 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	33.79	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5907	2026-05-02 00:00:00	citi	IN-N-OUTTUCSONBROADWAY TUCSON AZ	9.78	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5908	2026-05-02 00:00:00	citi	WAL-MART #1291 TUCSON AZ	41.73	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5909	2026-05-02 00:00:00	citi	THE GIRLS ESTATE SALES TUCSON AZ	23.91	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5910	2026-05-02 00:00:00	citi	GOODWILL OF SO AZ HOUGHTOTUCSON AZ	14.99	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5911	2026-05-02 00:00:00	citi	IN-N-OUTTUCSONBROADWAY TUCSON AZ	28.21	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5912	2026-05-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	4793.20	Transfers	f	\N	\N	\N	\N	\N	\N	\N
5914	2026-05-04 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	30.88	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5915	2026-05-04 00:00:00	citi	WAL-MART #1612 TUCSON AZ	32.57	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5916	2026-05-04 00:00:00	citi	FOOD CITY #171 TUCSON AZ	56.68	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5917	2026-05-04 00:00:00	citi	WAL-MART #1612 TUCSON AZ	39.84	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5918	2026-05-05 00:00:00	citi	OFFER 04 PROMOTIONAL APR ENDED 05/04/26	NaN	39.84	Other	f	\N	\N	\N	\N	\N	\N	\N
5919	2026-05-05 00:00:00	citi	OFFER 04 PROMOTIONAL APR ENDED 05/04/26	NaN	30.88	Other	f	\N	\N	\N	\N	\N	\N	\N
5920	2026-05-05 00:00:00	citi	OFFER 04 PROMOTIONAL APR ENDED 05/04/26	NaN	32.57	Other	f	\N	\N	\N	\N	\N	\N	\N
5921	2026-05-05 00:00:00	citi	OFFER 04 PROMOTIONAL APR ENDED 05/04/26	NaN	16.29	Other	f	\N	\N	\N	\N	\N	\N	\N
5922	2026-05-05 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	10.85	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5923	2026-05-05 00:00:00	citi	OFFER 04 MOVED TO STANDARD PURCH	5806.36	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5924	2026-05-05 00:00:00	citi	OFFER 04 MOVED TO STANDARD PURCH	39.84	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5925	2026-05-05 00:00:00	citi	OFFER 04 MOVED TO STANDARD PURCH	30.88	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5926	2026-05-05 00:00:00	citi	OFFER 04 MOVED TO STANDARD PURCH	32.57	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5927	2026-05-05 00:00:00	citi	OFFER 04 MOVED TO STANDARD PURCH	16.29	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5928	2026-05-05 00:00:00	citi	EL SUPER # 10 TUCSON AZ	12.90	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5929	2026-05-05 00:00:00	citi	OFFER 04 PROMOTIONAL APR ENDED 05/04/26	NaN	5806.36	Other	f	\N	\N	\N	\N	\N	\N	\N
5930	2026-05-06 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	6.76	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5931	2026-05-06 00:00:00	citi	OFFER 04 PROMOTIONAL APR ENDED 05/04/26	NaN	56.68	Other	f	\N	\N	\N	\N	\N	\N	\N
5932	2026-05-06 00:00:00	citi	OFFER 04 MOVED TO STANDARD PURCH	56.68	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5933	2026-05-08 00:00:00	citi	SILVERADO ROOTER AND leroy@silveraAZ	653.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5934	2026-04-29 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 66140799 Manuel Salas	4.00	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
5935	2026-05-04 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
5936	2026-05-04 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 66336913 Manuel Salas	34.90	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
5937	2026-05-04 00:00:00	wellsfargo	Bank of America Mortgage 260501 P47705280 , Salas M	816.94	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
5938	2026-05-06 00:00:00	wellsfargo	ATT Payment 050526 728666002Epaye Manuel Salas	152.01	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5939	2026-04-17 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	128.10	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5940	2026-04-17 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5941	2026-04-20 00:00:00	chase	Irs Treas 310 Tax Ref PPD ID: 9111736959	NaN	4601.00	Income	f	\N	\N	\N	\N	\N	\N	\N
5943	2026-04-24 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4655.12	Income	f	\N	\N	\N	\N	\N	\N	\N
5944	2026-04-28 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	24.92	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5945	2026-04-28 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1377.75	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
5946	2026-04-28 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
5947	2026-04-28 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1795.51	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
5948	2026-04-29 00:00:00	chase	Zelle Payment To Highplanes Arena Jpm99Cexwk2O	75.00	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5950	2026-05-01 00:00:00	chase	Zelle Payment To Reyna Maria 28647574608	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
5951	2026-05-01 00:00:00	chase	Xoom Debit OID 39422070 Web ID: 1770510487	603.69	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
5952	2026-05-04 00:00:00	chase	Rocket Mortgage Loan 2093968 Web ID: 0000452701	1529.48	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5953	2026-05-04 00:00:00	chase	Zelle Payment From Yesenia Valenzuela 29065588590	NaN	1325.00	Real State	f	\N	\N	\N	\N	\N	\N	\N
5954	2026-05-04 00:00:00	chase	Citi Autopay Payment 292001837950158 Web ID: Citicardap	4793.20	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
5956	2026-05-04 00:00:00	chase	Honda Pmt 8004451358 PPD ID: A953472715	625.43	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5957	2026-05-05 00:00:00	chase	05/05 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
5958	2026-05-07 00:00:00	chase	Zelle Payment To Alma Shenk Jpm99Cg1Y8Au	1329.41	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5959	2026-05-08 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4661.08	Income	f	\N	\N	\N	\N	\N	\N	\N
5960	2026-05-08 00:00:00	chase	Zelle Payment To Alma Shenk Jpm99Cg60Dsg	300.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5961	2026-05-11 00:00:00	chase	Zelle Payment To Alma Shenk Jpm99Cgog5Q6	770.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5963	2026-05-15 00:00:00	chase	Zelle Payment To Highplanes Arena Jpm99Ch0Yz49	75.00	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5964	2026-05-18 00:00:00	chase	Zelle Payment From Dba Liliana Ocano Hair Dresser Bacze5Vwl2Sf	NaN	1450.00	Real State	f	\N	\N	\N	\N	\N	\N	\N
5965	2026-05-18 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	196.44	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5967	2026-05-18 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5968	2026-05-08 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	70.11	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5969	2026-05-08 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	171.76	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5970	2026-05-08 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	NaN	24.97	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5971	2026-05-08 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	17.11	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5972	2026-05-08 00:00:00	citi	AMAZON MKTPL*BF9NK68A2 Amzn.com/billWA	6.50	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5973	2026-05-08 00:00:00	citi	SQ *WATER MART #18 Tucson AZ	19.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5974	2026-05-08 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	22.82	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5962	2026-05-13 00:00:00	chase	Zelle Payment From Allan C Sanceau Usbezs3S5Jcl	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
5942	2026-04-20 00:00:00	chase	Zelle Payment To Ruben Soto Jpm99Cdv7Rvh	1250.00	NaN	Home Improvement	f	\N	3	\N	\N	\N	\N	\N
5975	2026-05-08 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	198.12	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5976	2026-05-09 00:00:00	citi	ALIMENTOS Y COYOTAS DO HERMOSILLO SOMX	22.73	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5977	2026-05-09 00:00:00	citi	FERRETERIA CL HERMOSILLO SOMX	3.50	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
5978	2026-05-09 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	61.15	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5979	2026-05-09 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	15.85	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5980	2026-05-09 00:00:00	citi	REST ASADERO PURO PA D HERMOSILLO SOMX	15.74	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5981	2026-05-09 00:00:00	citi	FARM DARA LOPEZ PORTIL HERMOSILLO SOMX	10.84	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
5982	2026-05-09 00:00:00	citi	REST ASADERO PURO PA D HERMOSILLO SOMX	16.32	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5983	2026-05-10 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	11.37	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5984	2026-05-10 00:00:00	citi	SUPER STAR CAR WASH VALE 623-536-5956 AZ	20.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5985	2026-05-10 00:00:00	citi	FONDA EL JAVIAN URES SON MX	61.49	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
5986	2026-05-11 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	57.39	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5987	2026-05-11 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	57.02	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5988	2026-05-11 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	115.74	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5989	2026-05-12 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5990	2026-05-12 00:00:00	citi	SAVERS - 1051 TUCSON AZ	29.33	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5991	2026-05-13 00:00:00	citi	WM SUPERCENTER #5858 TUCSON AZ	35.97	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
5992	2026-05-13 00:00:00	citi	ROSS STORES #1971 TUCSON AZ	4.35	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5993	2026-05-13 00:00:00	citi	SILVERADO ROOTER AND leroy@silveraAZ	1092.13	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
5994	2026-05-13 00:00:00	citi	T.J. MAXX #1465 TUCSON AZ	NaN	23.91	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5995	2026-05-13 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	85.20	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
5996	2026-05-13 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	65.22	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
5999	2026-05-15 00:00:00	citi	ROSS STORES #999 TUCSON AZ	19.56	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6000	2026-05-15 00:00:00	citi	WAL-MART #4490 TUCSON AZ	31.17	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6001	2026-05-15 00:00:00	citi	WAL-MART #4490 TUCSON AZ	14.70	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6002	2026-05-15 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	17.67	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6003	2026-05-15 00:00:00	citi	DOLLAR TREE TUCSON AZ	1.36	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6004	2026-05-15 00:00:00	citi	BURLINGTON STORES 754 TUCSON AZ	NaN	46.51	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6005	2026-05-15 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	6.50	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6006	2026-05-16 00:00:00	citi	FRYS-FOOD-DRG #058 TUCSON AZ	8.97	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6007	2026-05-16 00:00:00	citi	LITTLE CAESARS #3168 800-722-3727 AZ	33.65	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6008	2026-05-16 00:00:00	citi	MCDONALD'S F39562 TUCSON AZ	4.86	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6009	2026-05-17 00:00:00	citi	SAMS CLUB #6692 TUCSON AZ	98.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6010	2026-05-17 00:00:00	citi	GOODWILL ARIZONA - ORACLETUCSON AZ	31.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6011	2026-05-17 00:00:00	citi	AZIAN 520-7778311 AZ	89.16	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6012	2026-05-17 00:00:00	citi	SAMS CLUB #6692 TUCSON AZ	21.72	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6013	2026-05-18 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	3.10	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6014	2026-05-18 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	2.18	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6015	2026-05-19 00:00:00	citi	FOOD CITY #156 TUCSON AZ	15.94	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6016	2026-05-19 00:00:00	citi	JCPENNEY 2913 TUCSON AZ	27.17	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6017	2026-05-19 00:00:00	citi	BURLINGTON STORES 1250 TUCSON AZ	31.50	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6018	2026-05-20 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	123.89	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6019	2026-05-20 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	116.06	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6020	2026-05-20 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	61.02	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6021	2026-05-20 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	15.04	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6022	2026-05-20 00:00:00	citi	WAL-MART #4490 TUCSON AZ	46.84	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6023	2026-05-21 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	1.09	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6024	2026-05-22 00:00:00	citi	CRUMBL THE LANDINGS 180-14101313 UT	31.15	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6025	2026-05-22 00:00:00	citi	STARBUCKS STORE 71737 TUCSON AZ	48.86	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6026	2026-05-22 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	24.18	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6027	2026-05-22 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	10.30	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6028	2026-05-22 00:00:00	citi	REST ASADERO PURO PA D HERMOSILLO SOMX	43.39	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6029	2026-05-23 00:00:00	citi	PANADERIA GODINEZ HERMOSILLO SOMX	14.58	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6030	2026-05-23 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	26.04	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6031	2026-05-23 00:00:00	citi	REST ASADERO PURO PA D HERMOSILLO SOMX	26.90	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6032	2026-05-23 00:00:00	citi	SILVERADO ROOTER AND leroy@silveraAZ	384.50	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6033	2026-05-23 00:00:00	citi	REYES HERMOSILLO SOMX	1.15	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6034	2026-05-23 00:00:00	citi	FLOR DE MAIZ TORTILLER HERMOSILLO MX	5.03	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6035	2026-05-24 00:00:00	citi	SERV EL FARO HERMOSILLO SOMX	71.17	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6036	2026-05-25 00:00:00	citi	PANDA EXPRESS #2055 NOGALES AZ	22.91	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6037	2026-05-25 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	95.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6038	2026-05-25 00:00:00	citi	SUPER PAZ MART URES SON MX	16.40	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6039	2026-05-25 00:00:00	citi	SUPER PAZ MART URES SON MX	25.74	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6040	2026-05-26 00:00:00	citi	SUPER PAZ MART URES SON MX	52.53	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6041	2026-05-26 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	6000.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6042	2026-05-27 00:00:00	citi	TELCEL DAR2 DAR VELOZC URES SON MX	23.13	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6043	2026-05-27 00:00:00	citi	SUPER PAZ MART URES SON MX	40.02	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6044	2026-05-27 00:00:00	citi	FARM SIMI URES 3 SON URES SON MX	29.34	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6045	2026-05-27 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	2.32	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6046	2026-05-28 00:00:00	citi	FERRO MATERIALES II URES SON MX	19.83	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6047	2026-05-29 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	4000.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6048	2026-05-29 00:00:00	citi	SUPER PAZ MART URES SON MX	28.06	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6049	2026-05-29 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	525.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6050	2026-05-30 00:00:00	citi	FERRO MATERIALES ESTRE URES SON MX	5.50	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6051	2026-05-31 00:00:00	citi	SUPER PAZ MART URES SON MX	20.35	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6052	2026-06-01 00:00:00	citi	SUPER PAZ MART URES SON MX	7.47	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6053	2026-06-02 00:00:00	citi	M A S CARWASH HERMOSILLO SOMX	10.14	NaN	Car Maintenance	f	\N	\N	\N	\N	\N	\N	\N
6054	2026-06-02 00:00:00	citi	BENAVIDES LA PALOMA HERMOSILLO SOMX	38.53	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6055	2026-06-02 00:00:00	citi	NIKKORI MORELOS TPV HERMOSILLO SOMX	48.31	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6058	2026-06-03 00:00:00	citi	CLIP MX*ROOT BEER GIL HERMOSILLO MX	2.32	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6059	2026-06-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	6398.98	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6060	2026-06-04 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	28.34	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6062	2026-06-04 00:00:00	citi	ABARROTES LUIS II HERMOSILLO SOMX	1.74	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6063	2026-06-04 00:00:00	citi	WUZIPAY*CLIN DORANTES CANCUN QROO MX	44.45	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6065	2026-06-04 00:00:00	citi	PIZZA PROGRESO 3 HERMOSILLO SOMX	16.10	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6066	2026-06-05 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	44.92	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6067	2026-06-05 00:00:00	citi	MERPAGO*TAQUEVICTOR2 CIUDAD DE MEXMX	40.57	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6068	2026-06-05 00:00:00	citi	MERPAGO*LAPURAVIDA HERMOSILLO MX	23.75	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6069	2026-06-05 00:00:00	citi	ALIMENTOS AL DETALLE SOCIHermosillo MX	3.01	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6070	2026-06-05 00:00:00	citi	SORIANA91 BACHOCO HERMOSILLO SOMX	78.61	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6071	2026-06-05 00:00:00	citi	DANIZA SALON HERMOSILLO SOMX	30.12	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6072	2026-06-06 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	34.69	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6073	2026-06-07 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	25.80	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6074	2026-06-07 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	1450.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6075	2026-06-07 00:00:00	citi	DJV HEATING COOLING L info@djvhvac.AZ	95.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6076	2026-06-07 00:00:00	citi	REST ASIAN EXPRESS S J SANTA ANA SONMX	15.76	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6077	2026-06-02 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6078	2026-06-02 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 67144409 Manuel Salas	34.90	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6079	2026-06-02 00:00:00	wellsfargo	Bank of America Mortgage M08581054020 Salas M	816.94	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6080	2026-06-08 00:00:00	wellsfargo	ATT Payment 060526 271600002Epayj Manuel Salas	162.05	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6081	2026-05-21 00:00:00	chase	Zelle Payment To Highplanes Arena Jpm99Chs4P9Y	75.00	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6082	2026-05-22 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4702.84	Income	f	\N	\N	\N	\N	\N	\N	\N
6084	2026-05-27 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1795.51	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6085	2026-05-27 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1377.75	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6086	2026-05-27 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	25.03	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6087	2026-05-28 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6088	2026-06-01 00:00:00	chase	Zelle Payment To Reyna Maria 29032937226	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
6089	2026-06-02 00:00:00	chase	Rocket Mortgage Loan 2727376 Web ID: 0000452701	1529.48	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6091	2026-06-02 00:00:00	chase	Honda Pmt 8004451358 PPD ID: A953472715	625.43	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6093	2026-06-03 00:00:00	chase	Citi Autopay Payment 292029479320091 Web ID: Citicardap	6398.98	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6094	2026-06-05 00:00:00	chase	Zelle Payment From Yesenia Valenzuela 29505487700	NaN	1325.00	Real State	f	\N	\N	\N	\N	\N	\N	\N
6095	2026-06-05 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4816.44	Income	f	\N	\N	\N	\N	\N	\N	\N
6096	2026-06-05 00:00:00	chase	06/05 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6097	2026-06-08 00:00:00	chase	Zelle Payment To Liliana Ocano Jpm99Cjufqy5	1850.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6098	2026-06-08 00:00:00	chase	Zelle Payment To Liliana Ocano Jpm99Cjuffez	1450.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6099	2026-06-08 00:00:00	chase	Zelle Payment To Liliana Ocano Jpm99Cjuf9Uc	217.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6100	2026-06-08 00:00:00	chase	Zelle Payment To Liliana Ocano Jpm99Cjug88R	400.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6101	2026-06-08 00:00:00	chase	Zelle Payment To Alma Shenk Jpm99Ck2Gqbz	3174.10	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6102	2026-06-09 00:00:00	chase	Zelle Payment To Alma Shenk Jpm99Ck6It3J	1296.43	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6103	2026-06-10 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	13170.33	Income	f	\N	\N	\N	\N	\N	\N	\N
6057	2026-06-03 00:00:00	citi	MERPAGO*SAMANTHABELTRA HERMOSILLO MX	7.73	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6056	2026-06-03 00:00:00	citi	MERPAGO*MARCELOREYESJ CIUDAD DE MEXMX	18.20	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6083	2026-05-26 00:00:00	chase	Zelle Payment To Ruben Soto Jpm99Ci8Ldba	320.00	NaN	Home Improvement	f	\N	3	\N	\N	\N	\N	\N
6092	2026-06-03 00:00:00	chase	Zelle Payment To Ruben Soto Jpm99Cjf7Bjc	176.00	NaN	Home Improvement	f	\N	3	\N	\N	\N	\N	\N
6104	2026-06-11 00:00:00	chase	Zelle Payment To Alma Shenk Jpm99Ckgtuur	545.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6106	2026-06-15 00:00:00	chase	Xoom Debit OID 40065704 Web ID: 1770510487	603.69	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6107	2026-06-08 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	63.56	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6108	2026-06-09 00:00:00	citi	SUPER PAZ MART URES SON MX	20.56	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6109	2026-06-09 00:00:00	citi	OXXO CUMBRES HERMOSILLO SOMX	5.30	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6110	2026-06-09 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	115.74	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6111	2026-06-10 00:00:00	citi	SUPER PAZ MART URES SON MX	25.57	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6112	2026-06-10 00:00:00	citi	SUPER STAR CAR WASH VALE 623-536-5956 AZ	20.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6113	2026-06-10 00:00:00	citi	SUPER PAZ MART URES SON MX	16.40	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6114	2026-06-11 00:00:00	citi	EMPIRE 8145 TUCSON AZ	2.16	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6115	2026-06-11 00:00:00	citi	QT 1490 TUCSON AZ	39.77	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6116	2026-06-11 00:00:00	citi	SUPER PAZ MART URES SON MX	23.92	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6117	2026-06-12 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	47.56	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6118	2026-06-12 00:00:00	citi	SUPER PAZ MART URES SON MX	93.02	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6119	2026-06-12 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6120	2026-06-13 00:00:00	citi	RESTAURANTE LAS BUGAMB URES SON MX	111.52	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6122	2026-06-13 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	13.40	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6123	2026-06-13 00:00:00	citi	MERPAGO*TALABARTERIAG CIUDAD DE MEXMX	59.47	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6125	2026-06-15 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	10.87	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6126	2026-06-15 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	92.86	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6127	2026-06-15 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	4.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6128	2026-06-15 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	51.29	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6129	2026-06-16 00:00:00	citi	BURGER KING #6486 Q07 TUCSON AZ	8.70	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6130	2026-06-16 00:00:00	citi	WAL-MART #3884 TUCSON AZ	39.15	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6131	2026-06-16 00:00:00	citi	DD'S DISCOUNTS #5449 TUCSON AZ	34.20	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6132	2026-06-17 00:00:00	citi	DD'S DISCOUNTS #5195 TUCSON AZ	54.33	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6133	2026-06-18 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	5.85	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6134	2026-06-18 00:00:00	citi	LITTLE CAESARS #3153 800-722-3727 AZ	27.69	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6135	2026-06-18 00:00:00	citi	T.J. MAXX #1465 TUCSON AZ	27.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6136	2026-06-18 00:00:00	citi	McDonalds 43260 130-3810089 AZ	18.03	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6137	2026-06-18 00:00:00	citi	ZILLOW *RENT LISTINGS 866-961-2570 WA	39.99	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6138	2026-06-18 00:00:00	citi	WAL-MART #5858 TUCSON AZ	46.83	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6139	2026-06-19 00:00:00	citi	FACEBK *SR59UU5YX2 650-5434800 DE	4.61	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6140	2026-06-19 00:00:00	citi	TAQUERIA SARAHI IMURIS SON MX	41.75	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6141	2026-06-19 00:00:00	citi	REYES HERMOSILLO SOMX	9.98	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6142	2026-06-19 00:00:00	citi	TDA DE SERV MAR NOGALES SON MX	9.28	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6143	2026-06-19 00:00:00	citi	PETROLERA LTB NOGALES SON MX	36.17	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6144	2026-06-19 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	19.58	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6145	2026-06-20 00:00:00	citi	BOL SATELITE SA DE CV HERMOSILLO MX	4.61	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6146	2026-06-20 00:00:00	citi	NETPAY *GREASE MONKEY HERMOSILLO MX	197.03	NaN	Car Maintenance	f	\N	\N	\N	\N	\N	\N	\N
6147	2026-06-20 00:00:00	citi	ELSA GLORIAS REPOSTERI HERMOSILLO SOMX	27.18	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6148	2026-06-20 00:00:00	citi	BOL SATELITE SA DE CV HERMOSILLO MX	29.20	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6149	2026-06-20 00:00:00	citi	SORIANA91 BACHOCO HERMOSILLO SOMX	80.65	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6150	2026-06-20 00:00:00	citi	SORIANA91 BACHOCO HERMOSILLO SOMX	23.08	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6151	2026-06-20 00:00:00	citi	PESCADERIA EL CAPITAN HERMOSILLO SOMX	58.41	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6152	2026-06-20 00:00:00	citi	TDA DE TODO PARA UNAS HERMOSILLO SOMX	16.77	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6153	2026-06-20 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	18.48	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6154	2026-06-21 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	58.48	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6155	2026-06-21 00:00:00	citi	SAMS BLVD MORELOS HERMOSILLO SOMX	20.83	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6156	2026-06-21 00:00:00	citi	MERPAGO*4OLIVOS CIUDAD DE MEXMX	33.37	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6157	2026-06-21 00:00:00	citi	PANDA EXPRESS #2055 NOGALES AZ	30.19	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6158	2026-06-22 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	35.84	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6159	2026-06-22 00:00:00	citi	HARKINS TUCSON SPECT TUCSON AZ	17.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6160	2026-06-23 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	13.60	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6161	2026-06-23 00:00:00	citi	FACEBK *KSZUSUMYX2 650-5434800 DE	11.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6162	2026-06-23 00:00:00	citi	HARKINS TUCSON SPECT TUCSON AZ	7.75	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6163	2026-06-23 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	3.25	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6164	2026-06-23 00:00:00	citi	HARKINS TUCSON SPECT 480-627-7777 AZ	62.70	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6165	2026-06-24 00:00:00	citi	WM SUPERCENTER #5858 TUCSON AZ	111.71	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6166	2026-06-25 00:00:00	citi	FACEBK *HW3TRTVXX2 650-5434800 DE	11.00	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6167	2026-06-26 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	56.96	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6168	2026-06-26 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	210.81	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6169	2026-06-26 00:00:00	citi	BLVCK BOBA TEA TUCSON AZ	34.16	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6170	2026-06-27 00:00:00	citi	REYES HERMOSILLO SOMX	1.49	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6105	2026-06-15 00:00:00	chase	Zelle Payment From Allan C Sanceau Usbrrhhsemya	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
6171	2026-06-27 00:00:00	citi	FERRETERIA LA RUMBA HERMOSILLO SOMX	36.98	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6172	2026-06-27 00:00:00	citi	Primo Water Corporatio Vista CA	3.10	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6173	2026-06-27 00:00:00	citi	RAISING CANES 0458 TUCSON AZ	139.27	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6174	2026-06-27 00:00:00	citi	RAISING CANES 0458 TUCSON AZ	10.83	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6175	2026-06-27 00:00:00	citi	RESTAURANT ELBA I SANTA ANA SONMX	65.19	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6176	2026-06-27 00:00:00	citi	OXXO CUMBRES HERMOSILLO SOMX	2.75	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6177	2026-06-27 00:00:00	citi	OXXO CUMBRES HERMOSILLO SOMX	9.04	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6178	2026-06-27 00:00:00	citi	GASERV MORELOS HERMOSILLO SOMX	68.53	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6179	2026-06-28 00:00:00	citi	REST MONA CAFE HERMOSILLO SOMX	46.52	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6180	2026-06-28 00:00:00	citi	NAYAXX1*NAYAX SONORA V MEXICO DF MX	1.38	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6181	2026-06-28 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	11.82	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6182	2026-06-29 00:00:00	citi	NAYAXX1*NAYAX SONORA V MEXICO DF MX	1.15	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6183	2026-06-29 00:00:00	citi	FAR GUAD 2388 HERMOSILLO SOMX	44.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6184	2026-06-29 00:00:00	citi	SUPER PAZ MART URES SON MX	11.93	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6185	2026-06-30 00:00:00	citi	FONDA EL JAVIAN URES SON MX	14.33	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6186	2026-06-30 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	4.30	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6187	2026-06-30 00:00:00	citi	OLIVE GARDEN ZK 0021622 TUCSON AZ	40.83	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6188	2026-07-01 00:00:00	citi	WAL-MART #1325 TUCSON AZ	68.42	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6189	2026-07-01 00:00:00	citi	SAMSCLUB #6692 TUCSON AZ	77.44	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6190	2026-07-01 00:00:00	citi	SAMSCLUB #6692 TUCSON AZ	137.67	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6191	2026-07-01 00:00:00	citi	WM SUPERCENTER #1612 TUCSON AZ	12.96	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6192	2026-07-01 00:00:00	citi	WAL-MART #1612 TUCSON AZ	39.09	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6193	2026-07-01 00:00:00	citi	REST MI FONDITA NOGALES SON MX	27.50	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6194	2026-07-01 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	53.15	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6195	2026-07-01 00:00:00	citi	THE HOME DEPOT #0467 TUCSON AZ	48.89	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6196	2026-07-01 00:00:00	citi	WAL-MART #4490 TUCSON AZ	79.24	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6197	2026-07-01 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	NaN	41.30	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6198	2026-07-01 00:00:00	citi	SAMS CLUB #6692 TUCSON AZ	NaN	38.00	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6199	2026-07-01 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	64.69	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6200	2026-07-02 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	66.72	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6201	2026-07-03 00:00:00	citi	SUPER PAZ MART URES SON MX	9.52	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6202	2026-07-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	16727.49	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6203	2026-07-03 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	5.40	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6204	2026-07-03 00:00:00	citi	ABTS LA TDA URES SON MX	14.52	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6205	2026-07-04 00:00:00	citi	REYES HERMOSILLO SOMX	26.64	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6206	2026-07-04 00:00:00	citi	REYES HERMOSILLO SOMX	1.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6208	2026-07-05 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	1.72	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6209	2026-07-06 00:00:00	citi	WM SUPERCENTER #5626 TUCSON AZ	18.87	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6210	2026-07-06 00:00:00	citi	SUPER PAZ MART URES SON MX	10.76	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6211	2026-07-02 00:00:00	wellsfargo	Recurring Transfer From Jpmorgan Chase Bank, NA Chk	NaN	950.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6212	2026-07-02 00:00:00	wellsfargo	Canterbury Ranch Assn Dues 68067222 Manuel Salas	34.90	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6213	2026-07-02 00:00:00	wellsfargo	Bank of America Mortgage M08506781444 Salas M	816.94	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6214	2026-07-06 00:00:00	wellsfargo	Empire Vista Assn Dues 68330814 Manuel Salas	108.00	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6215	2026-07-07 00:00:00	wellsfargo	ATT Payment 070526 532240001Epayn Manuel Salas	162.05	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6216	2026-06-17 00:00:00	chase	Remote Online Deposit 1	NaN	21.94	Income	f	\N	\N	\N	\N	\N	\N	\N
6217	2026-06-17 00:00:00	chase	Planet Fitness T Iclub Fees PPD ID: G710602737	15.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6218	2026-06-18 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4816.33	Income	f	\N	\N	\N	\N	\N	\N	\N
6219	2026-06-22 00:00:00	chase	Tep Corporate De Snap Pmt PPD ID: A860062700	170.33	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6221	2026-06-24 00:00:00	chase	Zelle Payment To Adam (Landscape) Jpm99Cmh1Ol5	549.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6222	2026-06-24 00:00:00	chase	Zelle Payment To Adam (Landscape) Jpm99Cmh1Zr3	1.00	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6223	2026-06-26 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1795.51	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6224	2026-06-26 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1377.75	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6225	2026-06-29 00:00:00	chase	Zelle Payment To Reyna Maria Varela 29792529507	172.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
6226	2026-06-29 00:00:00	chase	Xoom Debit OID 40286002 Web ID: 1770510487	4023.99	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6227	2026-06-30 00:00:00	chase	Pima Fcu Transfer Xxxx387698 Web ID: 1272484289	1790.20	NaN	Real State	f	\N	\N	\N	\N	\N	\N	\N
6228	2026-06-30 00:00:00	chase	Southwest Gas Billpay PPD ID: 4880085720	23.03	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6229	2026-07-01 00:00:00	chase	Zelle Payment From Reyna Maria Varela Souffle 29841223469	NaN	77.44	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6230	2026-07-01 00:00:00	chase	Zelle Payment From Veronica Flores 29835342916	NaN	2000.00	Other	f	\N	\N	\N	\N	\N	\N	\N
6231	2026-07-01 00:00:00	chase	Zelle Payment To Reyna Maria 29437276461	385.00	NaN	Reyna	f	\N	\N	\N	\N	\N	\N	\N
6233	2026-07-02 00:00:00	chase	Rocket Mortgage Loan 3532196 Web ID: 0000452701	1529.48	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6220	2026-06-23 00:00:00	chase	Robinhood Debits 162496129 Web ID: 5326394001	1200.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6235	2026-07-02 00:00:00	chase	Komatsu America Payroll PPD ID: B941715128	NaN	4816.34	Income	f	\N	\N	\N	\N	\N	\N	\N
6236	2026-07-02 00:00:00	chase	Xoom Credit O PPD ID: 1770510487	NaN	4023.99	Other	f	\N	\N	\N	\N	\N	\N	\N
6237	2026-07-03 00:00:00	chase	Citi Autopay Payment 292055400990053 Web ID: Citicardap	16727.49	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6238	2026-07-03 00:00:00	chase	Zelle Payment From Yesenia Valenzuela 29863423636	NaN	1325.00	Real State	f	\N	\N	\N	\N	\N	\N	\N
6239	2026-07-06 00:00:00	chase	07/06 Transfer To Sav Xxxxx0997	25.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6240	2026-07-07 00:00:00	chase	Online Transfer From Sav ...0997 Transaction#: 29921918120	NaN	2000.00	Other	f	\N	\N	\N	\N	\N	\N	\N
6244	2026-07-13 00:00:00	chase	Southwest Gas Payment B26191112359462 Web ID: 4880085720	54.63	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6245	2026-07-14 00:00:00	chase	Tep Corporate De Snap Pmt 8969144713 Web ID: 8860062700	192.55	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6247	2026-07-09 00:00:00	citi	SUPER PAZ MART URES SON MX	43.32	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6248	2026-07-09 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	55.64	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6249	2026-07-09 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	11.70	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6250	2026-07-10 00:00:00	citi	SUPER PAZ MART URES SON MX	17.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6252	2026-07-10 00:00:00	citi	OXXO ALAMEDA MXL URES SON MX	4.05	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6253	2026-07-10 00:00:00	citi	SUPER STAR CAR WASH VALE 623-536-5956 AZ	20.00	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6254	2026-07-11 00:00:00	citi	SUPER PAZ MART URES SON MX	6.38	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6255	2026-07-11 00:00:00	citi	CELY ABARROTES HERMOSILLO SOMX	14.90	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6257	2026-07-11 00:00:00	citi	FERRO MATERIALES II URES SON MX	3.44	NaN	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6258	2026-07-11 00:00:00	citi	FONDA EL JAVIAN URES SON MX	19.19	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6259	2026-07-11 00:00:00	citi	ASADERO PURO PA DELANTE HERMOSILLO MX	70.39	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6260	2026-07-12 00:00:00	citi	ABARR TACUPETITO COLOS HERMOSILLO SOMX	35.11	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6261	2026-07-12 00:00:00	citi	ABTS LAS TORRES HERMOSILLO SOMX	33.29	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6262	2026-07-12 00:00:00	citi	TDA DE SERV MAR NOGALES SON MX	10.37	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6263	2026-07-12 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	83.80	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6264	2026-07-12 00:00:00	citi	PANDA EXPRESS #1837 TUCSON AZ	29.46	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6265	2026-07-13 00:00:00	citi	EL SUPER # 10 TUCSON AZ	50.52	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6266	2026-07-13 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	4.40	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6267	2026-07-13 00:00:00	citi	SAVERS - 1051 TUCSON AZ	14.90	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6268	2026-07-13 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	11.92	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6269	2026-07-13 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	38.90	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6270	2026-07-13 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	60.83	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6271	2026-07-13 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	98.56	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6273	2026-07-13 00:00:00	citi	WAL MART BLVD MORELOS HERMOSILLO SOMX	12.22	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6274	2026-07-13 00:00:00	citi	ARCO BACHOCO HERMOSILLO SOMX	45.64	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6275	2026-07-13 00:00:00	citi	COX PHOENIX COMM SERV 800-234-3993 AZ	105.25	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6277	2026-07-14 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	52.48	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6278	2026-07-15 00:00:00	citi	TST*BEYOND BREAD - CENTR Tucson AZ	10.50	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6280	2026-07-15 00:00:00	citi	ROSS STORES #1321 TUCSON AZ	5.42	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6281	2026-07-15 00:00:00	citi	ROSS STORES #2732 TUCSON AZ	84.74	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6283	2026-07-16 00:00:00	citi	ASADERO PURO PA DELANTE HERMOSILLO MX	33.33	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6284	2026-07-16 00:00:00	citi	WAL-MART #4490 TUCSON AZ	22.69	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6285	2026-07-16 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	2.68	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6286	2026-07-17 00:00:00	citi	BURLINGTON STORES 1250 TUCSON AZ	155.28	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6287	2026-07-17 00:00:00	citi	ROSS STORES #1321 TUCSON AZ	114.08	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6288	2026-07-17 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	1.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6289	2026-07-18 00:00:00	citi	BURLINGTON STORES 754 TUCSON AZ	105.68	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6290	2026-07-18 00:00:00	citi	COSTCO GAS #0407 TUCSON AZ	61.58	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6292	2026-07-18 00:00:00	citi	WM SUPERCENTER #2922 TUCSON AZ	60.17	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6293	2026-07-18 00:00:00	citi	ROSS STORES #1971 TUCSON AZ	5.44	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6294	2026-07-18 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	38.01	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6296	2026-07-18 00:00:00	citi	ROSS STORES #1971 TUCSON AZ	NaN	5.21	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6298	2026-07-18 00:00:00	citi	IN-N-OUTTUCSON-I10/AJO TUCSON AZ	32.83	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6299	2026-07-19 00:00:00	citi	NEVERIA EL PATIO HERMOSILLO SOMX	19.76	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6300	2026-07-19 00:00:00	citi	MERPAGO*MARCELOREYESJ CIUDAD DE MEXMX	19.50	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6297	2026-07-18 00:00:00	citi	FACEBK *YCMDBWVYX2 650-5434800 DE	2.50	NaN	Real State	t	\N	\N	\N	\N	\N	\N	\N
6282	2026-07-15 00:00:00	citi	SUPER SALE BIN STORE TUCSON AZ	7.61	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6295	2026-07-18 00:00:00	citi	MERPAGO*MIGUEL HERMOSILLO MX	13.79	NaN	Groceries	t	\N	\N	\N	\N	\N	\N	\N
6291	2026-07-18 00:00:00	citi	Nike.com 800-8066453 CA	79.32	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6279	2026-07-15 00:00:00	citi	PROGRESSIVE INS 800-776-4737 OH	582.00	NaN	Utilities	t	\N	\N	\N	\N	\N	6	2026-07-14
6243	2026-07-13 00:00:00	chase	Zelle Payment From Allan C Sanceau Usb0Vbfsmufo	NaN	2000.00	Real State	f	\N	2	\N	\N	\N	\N	\N
6256	2026-07-11 00:00:00	citi	MERPAGO*DONGABRIEL HERMOSILLO MX	6.59	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6242	2026-07-09 00:00:00	chase	Robinhood Debits 162496129 Web ID: 5326394001	2000.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6246	2026-07-08 00:00:00	citi	USPS PO 0388910739 TUCSON AZ	11.17	NaN	Real State	t	\N	3	\N	\N	\N	\N	\N
6241	2026-07-08 00:00:00	chase	Zelle Payment From Jose Soto Bacy605Ihhok	NaN	2035.00	Real State	f	\N	3	\N	\N	\N	\N	\N
6301	2026-07-19 00:00:00	citi	GAS VIP SAN JUDAS SANTA ANA SONMX	12.52	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6302	2026-07-19 00:00:00	citi	MCDONALD'S F43260 TUCSON AZ	16.30	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6303	2026-07-19 00:00:00	citi	REYES HERMOSILLO SOMX	4.16	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6304	2026-07-19 00:00:00	citi	FAR GUAD 2388 HERMOSILLO SOMX	3.59	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6305	2026-07-20 00:00:00	citi	UBER *TRIP HELP.UBER.COM Ciudad de MexMX	2.85	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6308	2026-07-21 00:00:00	citi	MERPAGO*LAPURAVIDA HERMOSILLO MX	21.26	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6309	2026-07-21 00:00:00	citi	GASOL LPSA HERMOSILLO SOMX	92.36	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6311	2026-07-21 00:00:00	citi	ARRIVE: 00/00/00 DEPART: 00/00/00	15.20	NaN	Other	f	\N	\N	\N	\N	\N	\N	\N
6312	2026-07-22 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	16.29	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6313	2026-07-22 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	72.45	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6314	2026-07-23 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	31.96	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6315	2026-07-23 00:00:00	citi	AMAZON MKTPL*II0SM8X63 Amzn.com/billWA	10.86	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6316	2026-07-23 00:00:00	citi	WAL-MART #4490 TUCSON AZ	13.40	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6317	2026-07-23 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	NaN	5.36	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6318	2026-07-23 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	1.94	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6320	2026-07-24 00:00:00	citi	WAL-MART #2112 SCOTTSDALE AZ	90.74	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6321	2026-07-24 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	52.55	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6322	2026-07-24 00:00:00	citi	Cracker Barrel 800-3339963 TN	90.45	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6324	2026-07-25 00:00:00	citi	TARGET T-0363 SCOTTSDALE AZ	6.09	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6326	2026-07-26 00:00:00	citi	EL SUPER # 10 TUCSON AZ	5.66	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6327	2026-07-26 00:00:00	citi	TST*BEYOND BREAD - NORTH Tucson AZ	10.50	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6328	2026-07-26 00:00:00	citi	TST*CARNICERIA WILD WEST Tucson AZ	96.56	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6330	2026-07-27 00:00:00	citi	LAURA PILATES HERMOSILLO MX	35.79	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6331	2026-07-27 00:00:00	citi	WAL-MART #5626 TUCSON AZ	89.55	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6332	2026-07-27 00:00:00	citi	DAIRY QUEEN #17787 TUCSON AZ	14.09	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6336	2026-07-28 00:00:00	citi	WAL-MART #5626 TUCSON AZ	113.65	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6337	2026-07-28 00:00:00	citi	AMAZON MKTPL*R95FC1KI3 Amzn.com/billWA	19.99	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6338	2026-07-28 00:00:00	citi	AMAZON MKTPL*AP6F31V83 Amzn.com/billWA	28.87	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6340	2026-07-28 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	64.28	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6341	2026-07-28 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	247.51	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6342	2026-07-29 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	7.50	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6343	2026-07-29 00:00:00	citi	AMAZON MKTPL*3X4J30FO3 Amzn.com/billWA	38.08	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6344	2026-07-29 00:00:00	citi	FRYS-FOOD-DRG #058 TUCSON AZ	37.86	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6345	2026-07-29 00:00:00	citi	WM SUPERCENTER #4490 TUCSON AZ	1.09	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6346	2026-07-29 00:00:00	citi	FOOD CITY #171 TUCSON AZ	7.45	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6347	2026-07-29 00:00:00	citi	WAL-MART #4490 TUCSON AZ	53.95	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6348	2026-07-30 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	3.80	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6349	2026-07-31 00:00:00	citi	TJMAXX #0665 TUCSON AZ	37.10	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6350	2026-07-31 00:00:00	citi	DAIRY QUEEN #15909 TUCSON AZ	9.42	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6351	2026-07-31 00:00:00	citi	ROSS STORES #2777 TUCSON AZ	92.24	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6352	2026-08-01 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	71.93	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6353	2026-08-01 00:00:00	citi	FRYS-FOOD-DRG #0087 LAVEEN AZ	11.99	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6355	2026-08-02 00:00:00	citi	CHARIOT PIZZA & GYROS TUCSON AZ	46.57	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6356	2026-08-02 00:00:00	citi	DAIRY QUEEN #15096 TUCSON AZ	19.96	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6357	2026-08-03 00:00:00	citi	WAL-MART #4490 TUCSON AZ	75.90	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6358	2026-08-03 00:00:00	citi	COSTCO GAS #1079 TUCSON AZ	46.90	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6359	2026-08-03 00:00:00	citi	COSTCO WHSE #1079 TUCSON AZ	93.01	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6360	2026-08-03 00:00:00	citi	AUTOPAY 999990000037199RAUTOPAY AUTO-PMT	NaN	3789.94	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6362	2026-08-04 00:00:00	citi	THE GIRLS ESTATE SALES TUCSON AZ	37.00	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6364	2026-08-05 00:00:00	citi	COSTCO WHSE #0431 TUCSON AZ	93.45	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6365	2026-08-05 00:00:00	citi	WAL-MART #2922 TUCSON AZ	10.09	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6366	2026-08-05 00:00:00	citi	TUCSON WATER 520-791-3242 AZ	103.21	NaN	Utilities	f	\N	\N	\N	\N	\N	\N	\N
6367	2026-08-05 00:00:00	citi	WAL-MART #4490 TUCSON AZ	21.92	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6339	2026-07-28 00:00:00	citi	SQ *MEGA PINATA LLC TUCSON AZ	62.98	NaN	Shopping	t	Pinata and candy	\N	\N	\N	\N	\N	\N
6354	2026-08-01 00:00:00	citi	ALDI 79157 LAVEEN AZ	3.79	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6335	2026-07-28 00:00:00	citi	GALLEGO PTA (PRIMA GALLEGOPTA.MEAZ	13.48	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6334	2026-07-27 00:00:00	citi	USPS PO 0388910739 TUCSON AZ	6.37	NaN	Real State	t	\N	3	\N	\N	\N	\N	\N
6333	2026-07-27 00:00:00	citi	SQ *KONA ICE OF MARANA Tucson AZ	4.34	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6310	2026-07-21 00:00:00	citi	GREAT WOLF LDG SCOTTSD SCOTTSDALE AZ	443.51	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6325	2026-07-26 00:00:00	citi	GREAT WOLF LDG SCOTTSD SCOTTSDALE AZ	986.67	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6323	2026-07-25 00:00:00	citi	P.F.CHANG'S 9978 POS SCOTTSDALE AZ	111.39	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6319	2026-07-24 00:00:00	citi	GWL SCOTTSDALE WOODS E 480-9489653 AZ	28.83	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6307	2026-07-20 00:00:00	citi	MERPAGO*TODOPARALATAP HERMOSILLO MX	6.95	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6306	2026-07-20 00:00:00	citi	MERPAGO*SAMANTHABELTRA HERMOSILLO MX	33.39	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
6368	2026-08-06 00:00:00	citi	TUTTI FRUTTI FROZEN YOGURTUCSON AZ	19.14	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6369	2026-08-06 00:00:00	citi	QT 1499 OUTSIDE TUCSON AZ	27.75	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6372	2026-08-06 00:00:00	citi	GASERV MORELOS 3 HERMOSILLO SOMX	47.91	NaN	Transport/Gas	f	\N	\N	\N	\N	\N	\N	\N
6374	2026-08-07 00:00:00	citi	SUPER CARNICERIA EL RODEOTUCSON AZ	89.70	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6375	2026-08-07 00:00:00	citi	DOLLAR GENERAL #20744 TUCSON AZ	16.75	NaN	Groceries	f	\N	\N	\N	\N	\N	\N	\N
6376	2026-08-07 00:00:00	citi	JERRY BOB'S RESTAURANT TUCSON AZ	43.00	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6379	2026-08-07 00:00:00	citi	SARKU JAPAN 138 TUCSON AZ	16.83	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6381	2026-08-08 00:00:00	citi	PANDA EXPRESS #3525 TUCSON AZ	32.39	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6383	2026-08-08 00:00:00	citi	THE HOME DEPOT #0410 TUCSON AZ	NaN	38.75	Home Improvement	f	\N	\N	\N	\N	\N	\N	\N
6385	2026-08-09 00:00:00	citi	CINEMARK 435 BOXCON Tucson AZ	53.26	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6386	2026-08-09 00:00:00	citi	CINEMARK 435 RSTBAR Tucson AZ	11.41	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6387	2026-08-09 00:00:00	citi	SALVATION ARMY 430 ST16 TUCSON AZ	21.71	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1310	2025-12-13 00:00:00	citi	Netflix 1 8445052993 CA	19.56	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
1449	2026-01-13 00:00:00	citi	Netflix.com 866-5797172 CA	19.56	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
1772	2026-03-13 00:00:00	citi	Netflix 1 8445052993 CA	19.56	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
5820	2026-04-13 00:00:00	citi	Netflix.com netflix.com CA	19.56	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
5997	2026-05-13 00:00:00	citi	Netflix.com netflix.com CA	21.73	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
6121	2026-06-13 00:00:00	citi	Netflix 1 8445052993 CA	21.73	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
6272	2026-07-13 00:00:00	citi	Netflix.com 408-5403700 CA	21.73	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
6388	2026-08-10 00:00:00	citi	WWW.READING.COM SAN JUAN PR	12.49	NaN	Digital Subscriptions	f	\N	\N	\N	\N	\N	\N	\N
6251	2026-07-10 00:00:00	citi	WWW.READING.COM SAN JUAN PR	12.49	NaN	Digital Subscriptions	t	Reading app online	\N	\N	\N	\N	\N	\N
6384	2026-08-08 00:00:00	citi	THE HOME DEPOT #0410 TUCSON AZ	41.02	NaN	Home Improvement	t	Irrigation valves	\N	\N	\N	\N	\N	\N
6382	2026-08-08 00:00:00	citi	ACE HARDWARE TUCSON TUCSON AZ	32.60	NaN	Home Improvement	t	Irrigation valve	\N	\N	\N	\N	\N	\N
1326	2025-12-16 00:00:00	citi	AMAZON MKTPLACE PMTS Amzn.com/billWA	NaN	10.86	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1824	2026-03-22 00:00:00	citi	AMAZON RETA* B519U5OJ1 WWW.AMAZON.COWA	36.02	NaN	Shopping	t	AC Filters Willow	\N	\N	\N	\N	\N	\N
6370	2026-08-06 00:00:00	citi	VICTORIA'S SECRET 0458 TUCSON AZ	86.91	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6378	2026-08-07 00:00:00	citi	VICTORIA'S SECRET 0458 TUCSON AZ	NaN	21.74	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1931	2026-03-09 00:00:00	banamex	PAGO INTERBANCARIO A Mercado Pago W AL BENEF. EVERARDO,BOJORQIEZ/SANDOVAL (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 722969010407246106 CLAVE RASTREO 085904454234306660 REF. 0070326 Odyssey asiento MISMO DIA	27.03	NaN	Shopping	t	Odyssey back sit repair	\N	\N	\N	\N	\N	\N
5850	2026-04-18 00:00:00	citi	CTLP*CARRAZCO LLC TUSCON AZ	1.25	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6380	2026-08-07 00:00:00	citi	CTLP*CARRAZCO LLC TUCSON AZ	1.25	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6377	2026-08-07 00:00:00	citi	Lovisa 50303 Tuscon AZ	24.99	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6371	2026-08-06 00:00:00	citi	ULTA #170 TUCSON AZ	66.28	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1930	2026-03-09 00:00:00	banamex	PAGO INTERBANCARIO A Mercado Pago W AL BENEF. RUBEN,IBARRA/TORRES (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 722969010527184944 CLAVE RASTREO 085904199764306661 REF. 0070326 frenos tacoma MISMO DIA	159.19	NaN	Restaurants	t	Tacoma Breaks	\N	\N	\N	\N	\N	\N
1426	2025-12-22 00:00:00	banamex	PAGO INTERBANCARIO A BANCOPPEL AL BENEF. MIGUEL,RUIZ/SUSHI (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 004169161470429027 CLAVE RASTREO 085900778334335657 REF. 0221225 sushi MISMO DIA	58.38	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6373	2026-08-06 00:00:00	citi	FARM JOSE MANUEL ROBLE HERMOSILLO SOMX	5.29	NaN	Pharmacy/Health	f	\N	3	\N	\N	\N	\N	\N
1779	2026-03-14 00:00:00	citi	GOOGLE *Google One 855-836-3987 CA	2.16	NaN	Shopping	t	Google Cloud Service for Reyna	\N	\N	\N	\N	\N	\N
1881	2026-04-04 00:00:00	citi	AMAZON PRIME*8077M64Y3 Amzn.com/billWA	16.29	NaN	Shopping	t	\N	\N	\N	\N	\N	\N	\N
1455	2026-01-14 00:00:00	citi	GOOGLE *Google One 855-836-3987 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1610	2026-02-14 00:00:00	citi	GOOGLE *Google One 855-836-3987 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6363	2026-08-04 00:00:00	citi	THE HOME DEPOT #0474 TUCSON AZ	45.21	NaN	Home Improvement	t	Irrigation valves	\N	\N	\N	\N	\N	\N
6361	2026-08-04 00:00:00	citi	AMAZON PRIME*OY2MK2ZF3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1794	2026-03-16 00:00:00	citi	Google One 650-2530000 CA	32.60	NaN	Shopping	f	Google Cloud Service	\N	\N	\N	\N	\N	\N
1316	2025-12-14 00:00:00	citi	GOOGLE *Google One 855-836-3987 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5826	2026-04-15 00:00:00	citi	Google One 650-2530000 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1527	2026-02-04 00:00:00	citi	AMAZON PRIME*WX0ES4GN3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5913	2026-05-04 00:00:00	citi	AMAZON PRIME*UY3TE38G3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6061	2026-06-04 00:00:00	citi	AMAZON PRIME*C76TJ0AH3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6207	2026-07-04 00:00:00	citi	AMAZON PRIME*0N4L59NY3 Amzn.com/billWA	16.29	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
5998	2026-05-14 00:00:00	citi	Google One 650-2530000 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6124	2026-06-14 00:00:00	citi	Google One 650-2530000 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
6276	2026-07-14 00:00:00	citi	Google One 650-2530000 CA	2.16	NaN	Shopping	f	\N	\N	\N	\N	\N	\N	\N
1561	2026-01-29 00:00:00	chase	Zelle Payment To Brianna Jpm99C3L5Cxm	33.50	NaN	Restaurants	f	\N	\N	\N	\N	\N	\N	\N
6329	2026-07-26 00:00:00	citi	GREAT WOLF LDG SCOTTSD SCOTTSDALE AZ	66.63	NaN	Entertainment	f	\N	\N	\N	\N	\N	\N	\N
6064	2026-06-04 00:00:00	citi	MERPAGO*SAMANTHABELTRA CIUDAD DE MEXMX	27.05	NaN	Pharmacy/Health	f	\N	\N	\N	\N	\N	\N	\N
1933	2026-03-23 00:00:00	banamex	PAGO INTERBANCARIO A Mercado Pago W AL BENEF. RUBEN,IBARRA/TORRES (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 722969010527184944 CLAVE RASTREO 085904488144308068 REF. 0210326 frenos Odyssey MISMO DIA	89.14	NaN	Shopping	f	Odyssey Breaks	\N	\N	\N	\N	\N	\N
1736	2026-03-03 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0X32Gkth Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6232	2026-07-01 00:00:00	chase	ATM Cash Deposit 07/01 201 W Continental Rd Green Valley AZ Card 0187	NaN	2330.00	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6234	2026-07-02 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0Yqt2Ddw Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
5955	2026-05-04 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0Xw8Q6Kk Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
6090	2026-06-02 00:00:00	chase	Wells Fargo Ifi DDA To DDA Fp0Ybpm8Qx Web ID: Intfitrvos	950.00	NaN	Transfers	f	\N	\N	\N	\N	\N	\N	\N
1427	2025-12-24 00:00:00	banamex	PAGO INTERBANCARIO A BBVA MEXICO AL BENEF. JOSE MARTIN,ACEVEDO/ACEVEDO (DATO NO VERIFICADO POR ESTA INSTITUCION) CTA.BENEFICIARIO 004152314217961625 CLAVE RASTREO 085908689654335758 REF. 0231225 dogos MISMO DIA	26.76	NaN	Restaurants	f	\N	3	\N	\N	\N	\N	\N
1555	2026-01-26 00:00:00	chase	Zelle Payment From Jose Soto Bacy6Ycy7Xim	NaN	30.00	Real State	f	\N	3	\N	\N	\N	\N	\N
5949	2026-05-01 00:00:00	chase	Zelle Payment To Ruben Soto Jpm99Cf6R6Nx	370.00	NaN	Home Improvement	f	\N	3	\N	\N	\N	\N	\N
5966	2026-05-18 00:00:00	chase	Zelle Payment From Jose Souffle Ramirez Wfct1268Vrvw	NaN	200.00	Real State	f	\N	3	\N	\N	\N	\N	\N
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: salas
--

COPY public.categories (id, name, keywords) FROM stdin;
2	Reyna	["Zelle Payment To Reyna"]
5	Transport/Gas	["GAS", "UBER", "LYFT", "TRANSPORTE", "GASOLINERA", "QT", "ARCO", "COP PARKING METER", "CIRCLE K", "SHELL OIL", "GAZPRO", "CHEVRON", "COSTCO GAS", "GASERV", "AUTOPIS", "SPEEDWAY 1169", "SPEEDWAY 46268", "SPEEDWAY 46280", "SPEEDWAY 46261", "RCH AEROPUERTO", "UBRPAGOSMEX"]
6	Car Maintenance	["GREASE MONKEY", "EMISSIONS", "Emissions", "TOMMYS EXPRESS", "CAR WASH", "CARWASH", "TIRES", "AUTOPART DETA", "CHAPMAN HONDA", "AUTOZONE", "O'REILLY", "RUBEN,IBARRA/TORRES", "EVERARDO,BOJORQIEZ/SANDOVAL"]
7	Utilities	["AZ MVD FEE", "TELMEX", "CFE", "AGUA", "INTERNET", "LUZ", "ELECTRICIDAD", "TUCSON WATER", "COX", "ATT", "COSTCO *ANNUAL RENEWAL", "Costco Annual", "Netflix", "PROGRESSIVE", "AT&T", "Empire Vista Assn Dues", "EMPIRE 8145", "PAY-HOA ASSESSMENTS", "Dbamr.Cooper", "Rocket Mortgage", "Honda Pmt", "Tep Corporate", "Southwest Gas", "GOB EDO SONORA", "Zelle Payment To 5204278933"]
8	Home Improvement	["HOME DEPOT", "1335 HERMOSILLO", "INTERCERAMIC", "WINDOW DEPOT", "LOWES", "SHERWIN-WILLIAMS", "FERRE", "FERR KIOSKO MORELOS", "ACE", "RUBBERIZED COAT", "COMEX", "HERRAJES", "MATERIALES", "PIPESO", "PROCONSA PROGRESO", "LOS REALES SCALES", "HARBOR FREIGHT", "FLOOR AND DECOR", "Payment To Karina", "Payment To Ruben Soto", "Payment To D&C Maintenance LLC", "Payment To Carmen", "Payment To Ricardo", "Payment To Noe", "Payment To Francisco Herrera", "Payment To Jesus Encinas", "Payment To Ezequiel Pina", "Payment To Javier Herrera", "Payment To Ruben Peralta", "Payment To Efrain Carpintero", "Payment To Kristin Manning", "Payment To Manuel", "Payment To Martin Pesqueira", "Payment To Erick Gonzales", "RAY READY MIX", "IND METAL SUPPL", "DJV HEATING COOLING", "IMEXYACCESORIO"]
10	Travel	["VIVAAEROB", "HOLIDAY INN", "PSM PROSEPAGO", "HOTEL", "MUSEUM", "URBAN MILWAUKEE", "Localiza", "AIRBNB", "PARKMOBILE", "PARKING", "THE BRIDGE TRAVEL", "CASA/KINO", "ALMA ANAHI LIZARRAGA", "MUSEO JUAN GABRIEL", "ESTACION CARLOS AMAYA", "TOURPORJUAREZ", "USCIS"]
13	Real State	["AZ CORP COMMISSION", "DEVELOPMENT SERVICES", "UPS", "PIMA FEDERAL CREDIT", "USPS", "Bank of America Mortgage", "Canterbury Ranch Assn Dues", "Valencia Reserve Hoa Dues", "Pima Fcu Transfer", "ZILLOW", "Payment From Valdez Concrete LLC", "Payment From Iran Valdez", "Payment From Yolanda", "Payment From Carmen", "Payment From Yesenia", "Payment From Noe", "Payment From Jose", "Payment From Allan", "Payment From Dba Liliana Ocano"]
15	Income	["Modular Mining S Payroll", "Komatsu America Payroll", "Remote Online Deposit", "Costco Cash Reward", "Tax Ref"]
16	Papas	["GRACIELA,CARDENAS/QUINTERO"]
12	Entertainment	["AMC 2698 FOOTHILLS 15", "ANGEL WWW.ANGEL.COMUT", "CARNIVAL ONLINE PIMA", "TICKETS", "SKY PLACE", "CINEMARK", "KIDZANIA", "GRUTAS", "PARKS", "Elevate South Tucson", "TCC", "UNVRS* TUCSON HOLID", "GALLEGOINTERMEDIAT", "SQ *CABALLERO", "BOL SATELITE", "GREAT WOLF"]
11	Digital Subscriptions	["NETFLIX", "GOOGLE ONE", "EPICGAMES", "KWS AGE CHECK", "INTUIT", "Intuit", "READING.COM", "AMAZON PRIME"]
1	Groceries	["WALMART", "WAL-MART", "WAL MART", "HEB", "SUPER", "MERCADO", "GROCERY", "COSTCO COM", "COSTCO WHSE", "COSTCO HERMOSILLO", "SAMS", "LEY", "ABTS", "FRYS", "SAFEWAY", "DOLLAR", "BATHANDBODYWORKS", "bathandbodyworks", "FOOD CITY", "CTLP*CARRAZCO LLC", "LINDA VISTA", "SORIANA", "SQ *WATER MART", "SPROUTS", "REYES HERMOSILLO", "EL MARKET", "FRUTERIA", "DULCERIA", "ABTS LA CURVA", "PESCADERIA", "ABARROTES", "ALBERTSONS", "ALIMENTOS AL DETALLE", "MERPAGO*LAPURAVIDA", "MERPAGO*EFREN", "MERPAGO*GRANCHINA", "CARNICERIA", "ABARR TACUPETITO", "WHOLEFDS SPE", "S MART", "ALDI"]
4	Pharmacy/Health	["MEDICAL", "FARM", "GUAD", "PHARMACY", "FAR", "BIO PLASMA", "MB NAILS", "PLANET FITNESS", "Planet Fitness", "LAURA PILATES", "BARBERIA", "ARIZONA COMMUNITY PHYSIC", "KATS", "DANIZA SAL", "WALGREENS", "GENERAL DE LA BELLEZA", "SHELO NABEL HERMOSILLO", "FITMAX", "PELUQUER", "ESTET DON JUAN", "EXPRESSSCRI", "Highplanes Arena", "MERPAGO*SAMANTHABELTRA"]
14	Transfers	["AUTOPAY AUTO-PMT", "Citi Autopay Payment", "Recurring Transfer From Jpmorgan Chase Bank", "Wells Fargo Ifi DDA To DDA", "Transfer To Sav", "Xoom Debit", "Online Domestic Wire Transfer", "ATM Cash Deposit", "Payment From Rene", "Payment From Joaquin Samaniego", "Payment From Savannah", "Payment From Reyna Maria", "PAGO RECIBIDO DE TESORED POR ORDEN DE MANUEL SALAS", "DIS.EFE.BANAMEX SAB MIRADOR", "DIS.EFE.BANAMEX EL MIRADOR 2", "Umb Bank HSA", "Verification Olb Vtrans", "Robinhood Debits"]
9	Shopping	["BURLINGTON", "DD'S DISCOUNTS", "ROSS STORES", "MARSHALLS", "AMAZON", "Amazon", "MERCADO", "SAVERS", "SQ *THANK YOU FROM BELLA", "T.J. MAXX", "SHOP", "TIENDA", "CLIP MX*FLORERIA Y REG", "NALLELY SOBERANES PELU", "BONANZA DEALS", "BPK*JUAN DE DIOS", "GOODWILL", "DHRMA BAKTHI", "TARGET", "KOMATSU STORE", "GIRLS ESTATE SALES", "HOBBY-LOBBY", "SALVATION ARMY", "TJMAXX", "FLEXI", "BIN STORE", "CLIP MX*LOS DEL RAIL", "VAEROBUS", "OFERTAS DE ARAM", "Google One", "KWICK PLAZA DILA", "MEGA EDER", "OLD NAVY", "H&M", "CASA DE CAMPO URES", "INTER-STATE STUDIO", "XTRAMATH", "PAPELERIA", "DILLARDS", "CHICAGO MUSIC STORE", "IREPAIR XPERT", "OUTLET", "Carrazco LLC", "TEXAS GENERAL STORE", "JCPENNEY", "CARTER'S", "OADPRS MU", "ZAZUETA COMERCIAL", "POINTMP*REGALOS", "HABISTORE", "Nike US Stores", "TEKBUY", "COPPEL", "TELCEL", "PAYPAL *EBAY", "NOVEDAPICHAR", "SUBURBIA", "VICTORIA'S SECRET", "Lovisa", "ULTA", "MEGA PINATA", "GALLEGO PTA", "TODOPARALATAP", "MERPAGO*MARCELOREYESJ", "Nike.com"]
3	Restaurants	["RESTAURANT", "CAFE", "BURGER", "PIZZA", "DOGUITOS", "KFC", "MCDONALD", "McDonalds", "SUSHI", "WINGS", "DAIRY QUEEN", "IN-N-OUT", "FIVE GUYS", "DENNY'S", "TACO", "LITTLE CAESAR", "RAISING CANES", "MICHOACANA", "PANIFICADORA", "DILA GUAYMAS", "TDA DE SERV MAR", "AZIAN", "VIP SAN JUDAS", "FONDA EL JAVIAN URES", "NEVERIA EL PATIO", "OXXO", "CHARLEYS PHILLY", "PRETZELS", "OLIVE GARDEN", "BEYOND BREAD", "CHICK-FIL-A", "PANDA EXPRESS", "CA*GIRO AGREGADOR", "ASIAN EXPRESS", "STEAKHOUSE", "TAQUERIA", "DLR MARKET", "ICE CREAM", "TIANA'S PALACE", "CHURRO", "SNACK", "CANDY", "THE COVE ON HARBOR", "JACK IN THE BOX", "CAFFENIO", "MIYAGI", "COCINA", "PANADERIA", "POINTMP*OCHOAS", "YASAEL,OCHOA/OCHOA", "MERPAGO*OCHOAS", "CHICKENUEVO", "DINER", "DUNKIN", "BREW CITY BRAND", "MARISCOS", "SARKU", "GOLDEN CORRAL", "CACHORIADAS", "CENADURIA", "PEI WEI", "BAKERY", "TABU", "CHABELON", "CA FUNG", "BUFFALO", "REST", "JUGOS", "MUSCERA", "QUESERIA", "STARBUCKS", "REYDEREYES", "ACO HERMOSILLO", "COMERCIAL GALO", "LILIANMICHEL", "CHURRERIAS", "ELPATIOMODELO", "OREGANOS", "GELATO", "FIRST WATCH", "REPOSTERI", "POLLO", "ASADERO", "CHEDDAR", "ITALIAN PEASANT", "Cracker Barrel", "EEGEES", "YOGIS GRILL", "BURRITO", "TUTTI FRUTTI", "HOTDOGS", "HOT DOGS", "CAYOMANGO", "EL PARGO ROJO", "PIZZERIA", "PURO PA DELANTE", "COYOTAS DONA MARIA", "GIBSON GIRL ICE", "NIKKORI", "CUPBOP KINO", "SWEETTOMATOES", "BUFFET", "BISBEE BREAKFAST", "KRISPY KREME", "FOOD STAREVENT", "KE BURROS", "Payment To Brianna", "Payment To Rene", "Payment To Ulises", "Payment To Perro Loco Ajo", "Payment From Luz Venegas", "MARIA MAGDALENA,VALENZUELA/ROMO", "BRIANEN,BALDENEGRO/BALDENEGRO", "JOSE MARTIN,ACEVEDO/ACEVEDO", "CARNITAS LA YOCA", "NEVERIAPARQUE", "7 ELEVEN", "SUBWAY", "CHIPOTLE", "YOLOPAY*VENDING", "TACARBON", "CASA GARMENDIA", "CHUERRERIA", "DONVI", "LOMASANMIGUEL", "PILOT 593", "APPLEBBEES", "EL MANDIL SONORENSE", "CITY SALADS", "TCONE AGREGADOR", "SALAD AND GO", "KONA ICE", "P.F.CHANG'S", "GWL SCOTTSDALE WOODS", "MERPAGO*DONGABRIEL"]
\.


--
-- Data for Name: rental_properties; Type: TABLE DATA; Schema: public; Owner: salas
--

COPY public.rental_properties (id, alias, address, tenant, lease_renewal_date, payment_day) FROM stdin;
1	Escalante	6743 E Escalante Rd, Tucson AZ 85730	Yesenia Valenzuela	2027-02-04	4
4	Kostka	4443 S Kostka Av, Tucson AZ 85714	Liliana Ocano	2027-04-13	14
2	Franklin	5953 E Franklin Tale Dr, Tucson AZ 85756	Allan C Sanceau	2027-09-11	12
3	Stonefield	6992 S Stonefield Dr, Tucson AZ 85756	Jose Soto	2027-03-20	21
\.


--
-- Data for Name: vehicle_services; Type: TABLE DATA; Schema: public; Owner: salas
--

COPY public.vehicle_services (id, vehicle_id, date, description, mileage) FROM stdin;
\.


--
-- Data for Name: vehicles; Type: TABLE DATA; Schema: public; Owner: salas
--

COPY public.vehicles (id, alias, make, model, year, registration_due_date) FROM stdin;
\.


--
-- Name: action_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salas
--

SELECT pg_catalog.setval('public.action_items_id_seq', 17, true);


--
-- Name: all_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salas
--

SELECT pg_catalog.setval('public.all_expenses_id_seq', 6388, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salas
--

SELECT pg_catalog.setval('public.categories_id_seq', 16, true);


--
-- Name: rental_properties_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salas
--

SELECT pg_catalog.setval('public.rental_properties_id_seq', 4, true);


--
-- Name: vehicle_services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salas
--

SELECT pg_catalog.setval('public.vehicle_services_id_seq', 1, false);


--
-- Name: vehicles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salas
--

SELECT pg_catalog.setval('public.vehicles_id_seq', 1, false);


--
-- Name: action_items action_items_action_key_key; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.action_items
    ADD CONSTRAINT action_items_action_key_key UNIQUE (action_key);


--
-- Name: action_items action_items_pkey; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.action_items
    ADD CONSTRAINT action_items_pkey PRIMARY KEY (id);


--
-- Name: all_expenses all_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.all_expenses
    ADD CONSTRAINT all_expenses_pkey PRIMARY KEY (id);


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: rental_properties rental_properties_alias_key; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.rental_properties
    ADD CONSTRAINT rental_properties_alias_key UNIQUE (alias);


--
-- Name: rental_properties rental_properties_pkey; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.rental_properties
    ADD CONSTRAINT rental_properties_pkey PRIMARY KEY (id);


--
-- Name: all_expenses uix_expense_natural_key; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.all_expenses
    ADD CONSTRAINT uix_expense_natural_key UNIQUE NULLS NOT DISTINCT (date, bank, description, debit, credit);


--
-- Name: vehicle_services vehicle_services_pkey; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.vehicle_services
    ADD CONSTRAINT vehicle_services_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_alias_key; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_alias_key UNIQUE (alias);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- Name: action_items action_items_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.action_items
    ADD CONSTRAINT action_items_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.rental_properties(id) ON DELETE SET NULL;


--
-- Name: all_expenses all_expenses_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.all_expenses
    ADD CONSTRAINT all_expenses_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.rental_properties(id) ON DELETE SET NULL;


--
-- Name: all_expenses all_expenses_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.all_expenses
    ADD CONSTRAINT all_expenses_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE SET NULL;


--
-- Name: vehicle_services vehicle_services_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: salas
--

ALTER TABLE ONLY public.vehicle_services
    ADD CONSTRAINT vehicle_services_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict TT31fbgce9XaL8lmFRMsJbxGvRyv8IEfAHpWoX2CyyNyNXile68mk6sqwvoZe6p

