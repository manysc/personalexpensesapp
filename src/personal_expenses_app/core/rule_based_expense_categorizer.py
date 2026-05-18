import logging

# Canonical mapping from category name → list of keyword substrings.
# This is the single source of truth used both by the rule-based categorizer
# and by the /categories/seed API endpoint to populate the database.
RULE_BASED_CATEGORIES: dict[str, list[str]] = {
    "Groceries": [
        "WALMART", "WAL-MART", "WAL MART", "HEB", "SUPER", "MERCADO",
        "GROCERY", "COSTCO COM", "COSTCO WHSE", "COSTCO HERMOSILLO", "SAMS",
        "LEY", "ABTS", "FRYS", "SAFEWAY", "DOLLAR", "BATHANDBODYWORKS",
        "bathandbodyworks", "FOOD CITY", "CTLP*CARRAZCO LLC", "LINDA VISTA",
        "SORIANA", "SQ *WATER MART", "SPROUTS", "REYES HERMOSILLO",
        "EL MARKET", "FRUTERIA", "DULCERIA", "ABTS LA CURVA", "PESCADERIA",
        "ABARROTES", "ALBERTSONS", "ALIMENTOS AL DETALLE",
        "MERPAGO*LAPURAVIDA", "MERPAGO*SAMANTHABELTRA", "MERPAGO*EFREN",
        "MERPAGO*GRANCHINA", "CARNICERIA", "ABARR TACUPETITO",
        "WHOLEFDS SPE", "S MART",
    ],
    "Reyna": ["Zelle Payment To Reyna"],
    "Restaurants": [
        "RESTAURANT", "CAFE", "BURGER", "PIZZA", "DOGUITOS", "KFC",
        "MCDONALD", "McDonalds", "SUSHI", "WINGS", "DAIRY QUEEN",
        "IN-N-OUT", "FIVE GUYS", "DENNY'S", "TACO", "LITTLE CAESAR",
        "RAISING CANES", "MICHOACANA", "PANIFICADORA", "DILA GUAYMAS",
        "TDA DE SERV MAR", "AZIAN", "VIP SAN JUDAS", "FONDA EL JAVIAN URES",
        "NEVERIA EL PATIO", "OXXO", "CHARLEYS PHILLY", "PRETZELS",
        "OLIVE GARDEN", "BEYOND BREAD", "CHICK-FIL-A", "PANDA EXPRESS",
        "CA*GIRO AGREGADOR", "ASIAN EXPRESS", "STEAKHOUSE", "TAQUERIA",
        "DLR MARKET", "ICE CREAM", "TIANA'S PALACE", "CHURRO", "SNACK",
        "CANDY", "THE COVE ON HARBOR", "JACK IN THE BOX", "CAFFENIO",
        "MIYAGI", "COCINA", "PANADERIA", "POINTMP*OCHOAS",
        "YASAEL,OCHOA/OCHOA", "MERPAGO*OCHOAS", "CHICKENUEVO", "DINER",
        "DUNKIN", "BREW CITY BRAND", "MARISCOS", "SARKU", "GOLDEN CORRAL",
        "CACHORIADAS", "CENADURIA", "PEI WEI", "BAKERY", "TABU",
        "CHABELON", "CA FUNG", "BUFFALO", "REST", "JUGOS", "MUSCERA",
        "QUESERIA", "STARBUCKS", "REYDEREYES", "ACO HERMOSILLO",
        "COMERCIAL GALO", "LILIANMICHEL", "CHURRERIAS", "ELPATIOMODELO",
        "OREGANOS", "GELATO", "FIRST WATCH", "REPOSTERI", "POLLO",
        "ASADERO", "CHEDDAR", "ITALIAN PEASANT", "Cracker Barrel", "EEGEES",
        "YOGIS GRILL", "BURRITO", "TUTTI FRUTTI", "HOTDOGS", "HOT DOGS",
        "CAYOMANGO", "EL PARGO ROJO", "PIZZERIA", "PURO PA DELANTE",
        "COYOTAS DONA MARIA", "GIBSON GIRL ICE", "NIKKORI", "CUPBOP KINO",
        "SWEETTOMATOES", "BUFFET", "BISBEE BREAKFAST", "KRISPY KREME",
        "FOOD STAREVENT", "KE BURROS", "Payment To Brianna",
        "Payment To Rene", "Payment To Ulises",
        "Payment To Perro Loco Ajo", "Payment From Luz Venegas",
        "MARIA MAGDALENA,VALENZUELA/ROMO",
        "BRIANEN,BALDENEGRO/BALDENEGRO", "JOSE MARTIN,ACEVEDO/ACEVEDO",
        "CARNITAS LA YOCA", "NEVERIAPARQUE", "7 ELEVEN", "SUBWAY",
        "CHIPOTLE", "YOLOPAY*VENDING", "TACARBON", "CASA GARMENDIA",
        "CHUERRERIA", "DONVI", "LOMASANMIGUEL", "PILOT 593", "APPLEBBEES",
        "EL MANDIL SONORENSE", "CITY SALADS", "TCONE AGREGADOR", "SALAD AND GO",
    ],
    "Pharmacy/Health": [
        "MEDICAL", "FARM", "GUAD", "PHARMACY", "FAR", "BIO PLASMA",
        "MB NAILS", "PLANET FITNESS", "Planet Fitness", "LAURA PILATES",
        "BARBERIA", "ARIZONA COMMUNITY PHYSIC", "KATS", "DANIZA SAL",
        "WALGREENS", "GENERAL DE LA BELLEZA", "SHELO NABEL HERMOSILLO",
        "FITMAX", "PELUQUER", "ESTET DON JUAN", "EXPRESSSCRI",
        "Highplanes Arena",
    ],
    "Transport/Gas": [
        "GAS", "UBER", "LYFT", "TRANSPORTE", "GASOLINERA", "QT", "ARCO",
        "COP PARKING METER", "CIRCLE K", "SHELL OIL", "GAZPRO", "CHEVRON",
        "COSTCO GAS", "GASERV", "AUTOPIS", "SPEEDWAY 1169",
        "SPEEDWAY 46268", "SPEEDWAY 46280", "SPEEDWAY 46261",
        "RCH AEROPUERTO", "UBRPAGOSMEX",
    ],
    "Car Maintenance": [
        "GREASE MONKEY", "EMISSIONS", "Emissions", "TOMMYS EXPRESS",
        "CAR WASH", "CARWASH", "TIRES", "AUTOPART DETA", "CHAPMAN HONDA",
        "AUTOZONE", "O'REILLY", "RUBEN,IBARRA/TORRES",
        "EVERARDO,BOJORQIEZ/SANDOVAL",
    ],
    "Utilities": [
        "AZ MVD FEE", "TELMEX", "CFE", "AGUA", "INTERNET", "LUZ",
        "ELECTRICIDAD", "TUCSON WATER", "COX", "ATT",
        "COSTCO *ANNUAL RENEWAL", "Costco Annual", "Netflix", "PROGRESSIVE",
        "AT&T", "Empire Vista Assn Dues", "EMPIRE 8145",
        "PAY-HOA ASSESSMENTS", "Dbamr.Cooper", "Rocket Mortgage",
        "Honda Pmt", "Tep Corporate", "Southwest Gas", "GOB EDO SONORA",
        "Zelle Payment To 5204278933",
    ],
    "Home Improvement": [
        "HOME DEPOT", "1335 HERMOSILLO", "INTERCERAMIC", "WINDOW DEPOT",
        "LOWES", "SHERWIN-WILLIAMS", "FERRE", "FERR KIOSKO MORELOS", "ACE",
        "RUBBERIZED COAT", "COMEX", "HERRAJES", "MATERIALES", "PIPESO",
        "PROCONSA PROGRESO", "LOS REALES SCALES", "HARBOR FREIGHT",
        "FLOOR AND DECOR", "Payment To Karina", "Payment To Ruben Soto",
        "Payment To D&C Maintenance LLC", "Payment To Carmen",
        "Payment To Ricardo", "Payment To Noe",
        "Payment To Francisco Herrera", "Payment To Jesus Encinas",
        "Payment To Ezequiel Pina", "Payment To Javier Herrera",
        "Payment To Ruben Peralta", "Payment To Efrain Carpintero",
        "Payment To Kristin Manning", "Payment To Manuel",
        "Payment To Martin Pesqueira", "Payment To Erick Gonzales",
        "RAY READY MIX", "IND METAL SUPPL", "DJV HEATING COOLING",
        "IMEXYACCESORIO",
    ],
    "Shopping": [
        "BURLINGTON", "DD'S DISCOUNTS", "ROSS STORES", "MARSHALLS",
        "AMAZON", "Amazon", "MERCADO", "SAVERS",
        "SQ *THANK YOU FROM BELLA", "T.J. MAXX", "SHOP", "TIENDA",
        "CLIP MX*FLORERIA Y REG", "NALLELY SOBERANES PELU", "BONANZA DEALS",
        "BPK*JUAN DE DIOS", "GOODWILL", "DHRMA BAKTHI", "TARGET",
        "KOMATSU STORE", "GIRLS ESTATE SALES", "HOBBY-LOBBY",
        "SALVATION ARMY", "TJMAXX", "FLEXI", "BIN STORE",
        "CLIP MX*LOS DEL RAIL", "VAEROBUS", "OFERTAS DE ARAM", "Google One",
        "KWICK PLAZA DILA", "MEGA EDER", "OLD NAVY", "H&M",
        "CASA DE CAMPO URES", "INTER-STATE STUDIO", "XTRAMATH", "PAPELERIA",
        "DILLARDS", "CHICAGO MUSIC STORE", "IREPAIR XPERT", "OUTLET",
        "Carrazco LLC", "TEXAS GENERAL STORE", "JCPENNEY", "CARTER'S",
        "OADPRS MU", "ZAZUETA COMERCIAL", "POINTMP*REGALOS", "HABISTORE",
        "Nike US Stores", "TEKBUY", "COPPEL", "TELCEL", "PAYPAL *EBAY",
        "NOVEDAPICHAR", "SUBURBIA",
    ],
    "Travel": [
        "VIVAAEROB", "HOLIDAY INN", "PSM PROSEPAGO", "HOTEL", "MUSEUM",
        "URBAN MILWAUKEE", "Localiza", "AIRBNB", "PARKMOBILE", "PARKING",
        "THE BRIDGE TRAVEL", "CASA/KINO", "ALMA ANAHI LIZARRAGA",
        "MUSEO JUAN GABRIEL", "ESTACION CARLOS AMAYA", "TOURPORJUAREZ",
        "USCIS",
    ],
    "Digital Subscriptions": [
        "NETFLIX", "GOOGLE ONE", "EPICGAMES", "KWS AGE CHECK", "INTUIT",
        "Intuit",
    ],
    "Entertainment": [
        "AMC 2698 FOOTHILLS 15", "ANGEL WWW.ANGEL.COMUT",
        "CARNIVAL ONLINE PIMA", "TICKETS", "SKY PLACE", "CINEMARK",
        "KIDZANIA", "GRUTAS", "PARKS", "Elevate South Tucson", "TCC",
        "UNVRS* TUCSON HOLID", "GALLEGOINTERMEDIAT", "SQ *CABALLERO",
        "BOL SATELITE",
    ],
    "Real State": [
        "AZ CORP COMMISSION", "DEVELOPMENT SERVICES", "UPS",
        "PIMA FEDERAL CREDIT", "USPS", "Bank of America Mortgage",
        "Canterbury Ranch Assn Dues", "Valencia Reserve Hoa Dues",
        "Pima Fcu Transfer", "ZILLOW",
        "Payment From Valdez Concrete LLC", "Payment From Iran Valdez",
        "Payment From Yolanda", "Payment From Carmen",
        "Payment From Yesenia", "Payment From Noe", "Payment From Jose",
        "Payment From Allan", "Payment From Dba Liliana Ocano",
    ],
    "Transfers": [
        "AUTOPAY AUTO-PMT", "Citi Autopay Payment",
        "Recurring Transfer From Jpmorgan Chase Bank",
        "Wells Fargo Ifi DDA To DDA", "Transfer To Sav", "Xoom Debit",
        "Online Domestic Wire Transfer", "ATM Cash Deposit",
        "Payment From Rene", "Payment From Joaquin Samaniego",
        "Payment From Savannah", "Payment From Reyna Maria",
        "PAGO RECIBIDO DE TESORED POR ORDEN DE MANUEL SALAS",
        "DIS.EFE.BANAMEX SAB MIRADOR", "DIS.EFE.BANAMEX EL MIRADOR 2",
        "Umb Bank HSA", "Verification Olb Vtrans",
    ],
    "Income": [
        "Modular Mining S Payroll", "Komatsu America Payroll",
        "Remote Online Deposit", "Costco Cash Reward", "Tax Ref",
    ],
    "Papas": ["GRACIELA,CARDENAS/QUINTERO"],
}


class RuleBasedExpenseCategorizer:
    def __init__(self):
        super().__init__()

    @staticmethod
    def _log_uncategorized_expense(row):
        """Log an expense that could not be categorized with full details."""
        print(
            f"WARNING: Could not categorize expense: "
            f"Date: {row['Date']}, "
            f"Bank: {row['Bank']}, "
            f"Description: {row['Description']}, "
            f"Debit: {row['Debit']}, "
            f"Credit: {row['Credit']}"
        )

    @staticmethod
    def _print_expense_details(row):
        """Format and print expense details for debugging."""
        print(
            f"Date: {row['Date']}, "
            f"Bank: {row['Bank']}, "
            f"Description: {row['Description']}, "
            f"Debit: {row['Debit']}, "
            f"Credit: {row['Credit']}, "
            f"Category: {row['Category']}"
        )

    @staticmethod
    def _rule_based_categorization(row):
        description = row["Description"]
        desc = str(description)
        for cat, keywords in RULE_BASED_CATEGORIES.items():
            for k in keywords:
                if k in desc:
                    return cat
        RuleBasedExpenseCategorizer._log_uncategorized_expense(row)
        return "Other"

    def categorize_expenses(self, df):
        df["Category"] = df.apply(self._rule_based_categorization, axis=1)
        # print description with amount and category for debugging
        # for index, row in df.iterrows():
        #     self._print_expense_details(row)
        return df
