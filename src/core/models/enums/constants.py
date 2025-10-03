"""Constants for data mapping and pattern matching."""

from typing import Dict, List
from src.core.models.enums.ieq_parameters import IEQParameter
from src.core.models.enums.building_enums import RoomType


# Default column mappings for common sensor data formats (multilingual)
DEFAULT_COLUMN_MAPPINGS: Dict[str, List[str]] = {
    IEQParameter.TEMPERATURE.value: [
        # English
        "temperature", "temp", "temperature_c", "temp_c", "air_temperature",
        "room_temperature", "indoor_temperature",
        # Danish/Norwegian
        "temperatur", "lufttemperatur", "romtemperatur",
        # German
        "temperatur", "lufttemperatur", "raumtemperatur", "innentemperatur",
        # French
        "température", "temp", "température_air", "température_ambiante",
        # Swedish
        "temperatur", "lufttemperatur", "rumstemperatur", "inomhustemperatur"
    ],
    IEQParameter.HUMIDITY.value: [
        # English
        "humidity", "rh", "relative_humidity", "humidity_percent", "rh_percent",
        "air_humidity", "indoor_humidity",
        # Danish/Norwegian
        "fugtighed", "luftfugtighed", "relativ_fugtighed",
        # German
        "feuchtigkeit", "luftfeuchtigkeit", "relative_feuchtigkeit", "raumfeuchtigkeit",
        # French
        "humidité", "humidité_relative", "humidité_air", "hr",
        # Swedish
        "fuktighet", "luftfuktighet", "relativ_fuktighet", "rumsfuktighet"
    ],
    IEQParameter.CO2.value: [
        # English
        "co2", "carbon_dioxide", "co2_ppm", "co2_concentration", "carbon_dioxide_ppm", "air_co2",
        # Danish/Norwegian
        "kuldioxid", "co2_koncentration", "luftkvalitet",
        # German
        "kohlendioxid", "kohlenstoffdioxid", "co2_gehalt", "luftqualität",
        # French
        "dioxyde_carbone", "co2_concentration", "qualité_air",
        # Swedish
        "koldioxid", "co2_halt", "luftkvalitet"
    ],
    IEQParameter.LIGHT.value: [
        # English
        "light", "lux", "illuminance", "light_level", "brightness", "lighting", "light_intensity",
        # Danish/Norwegian
        "lys", "belysning", "lysstyrke", "lysintensitet",
        # German
        "licht", "beleuchtung", "lichtstärke", "helligkeit", "beleuchtungsstärke",
        # French
        "lumière", "éclairage", "luminosité", "intensité_lumineuse", "éclairement",
        # Swedish
        "ljus", "belysning", "ljusstyrka", "ljusintensitet"
    ],
    IEQParameter.PRESENCE.value: [
        # English
        "presence", "occupancy", "motion", "pir", "people_count", "occupied",
        # Danish/Norwegian
        "tilstedeværelse", "nærvær", "bevægelse", "personer",
        # German
        "anwesenheit", "belegung", "bewegung", "personen", "präsenz",
        # French
        "présence", "occupation", "mouvement", "personnes", "détection",
        # Swedish
        "närvaro", "beläggning", "rörelse", "personer", "upptäckt"
    ],
    IEQParameter.TIMESTAMP.value: [
        # English
        "timestamp", "datetime", "time", "date_time", "date", "time_stamp", "measurement_time",
        # Danish/Norwegian
        "tidsstempel", "dato_tid", "måletid",
        # German
        "zeitstempel", "datum_zeit", "messzeit", "zeitpunkt",
        # French
        "horodatage", "date_heure", "temps_mesure", "timestamp",
        # Swedish
        "tidsstämpel", "datum_tid", "mättid"
    ]
}

# Building type patterns for room type inference (multilingual)
BUILDING_TYPE_PATTERNS: Dict[str, List[str]] = {
    "school": [
        # English
        "school", "academy", "college", "university", "educational",
        # Danish/Norwegian
        "skole", "skolen", "akademi", "uddannelse", "uddannelsesinstitution",
        # German
        "schule", "akademie", "universität", "bildung", "bildungseinrichtung",
        # French
        "école", "académie", "université", "éducation", "établissement_scolaire",
        # Swedish
        "skola", "akademi", "universitet", "utbildning", "utbildningsinstitution"
    ],
    "office": [
        # English
        "office", "business", "company", "corporate", "workplace",
        # Danish/Norwegian
        "kontor", "virksomhed", "forretning", "arbejdsplads",
        # German
        "büro", "unternehmen", "firma", "arbeitsplatz", "geschäft",
        # French
        "bureau", "entreprise", "société", "lieu_travail", "bureaux",
        # Swedish
        "kontor", "företag", "arbetsplats", "verksamhet"
    ],
    "hospital": [
        # English
        "hospital", "clinic", "medical", "healthcare", "health_center",
        # Danish/Norwegian
        "hospital", "klinik", "sundhed", "læge", "behandling",
        # German
        "krankenhaus", "klinik", "medizin", "gesundheit", "arzt",
        # French
        "hôpital", "clinique", "médical", "santé", "centre_santé",
        # Swedish
        "sjukhus", "klinik", "medicinsk", "hälsa", "vårdcentral"
    ]
}

# Room type patterns for specific room identification (multilingual)
ROOM_TYPE_PATTERNS: Dict[str, List[str]] = {
    RoomType.CLASSROOM.value: [
        # English
        "classroom", "class", "lecture", "teaching", "seminar",
        # Danish/Norwegian
        "klasseværelse", "klasse", "undervisning", "læring",
        # German
        "klassenzimmer", "klasse", "unterricht", "lehrsaal", "seminarraum",
        # French
        "salle_classe", "classe", "enseignement", "cours", "salle_cours",
        # Swedish
        "klassrum", "klass", "undervisning", "lärosal"
    ],
    RoomType.LIBRARY.value: [
        # English
        "library", "reading", "books", "study",
        # Danish/Norwegian
        "bibliotek", "læsning", "bøger", "studium",
        # German
        "bibliothek", "bücherei", "lesen", "bücher", "studium",
        # French
        "bibliothèque", "lecture", "livres", "étude",
        # Swedish
        "bibliotek", "läsning", "böcker", "studium"
    ],
    RoomType.CAFETERIA.value: [
        # English
        "cafeteria", "cafe", "canteen", "dining", "restaurant", "kitchen",
        # Danish/Norwegian
        "kantine", "café", "spisning", "køkken", "madsal",
        # German
        "kantine", "mensa", "café", "küche", "speisesaal", "restaurant",
        # French
        "cantine", "café", "restaurant", "cuisine", "salle_manger",
        # Swedish
        "kafeteria", "matsal", "café", "kök", "restaurang"
    ],
    RoomType.GYMNASIUM.value: [
        # English
        "gymnasium", "gym", "sports", "fitness", "exercise", "hall",
        # Danish/Norwegian
        "gymnastiksal", "idrætshal", "sport", "motion", "hal",
        # German
        "turnhalle", "sporthalle", "gymnastik", "sport", "fitness",
        # French
        "gymnase", "salle_sport", "fitness", "exercice", "sport",
        # Swedish
        "gymnastiksal", "idrottshall", "sport", "träning", "hall"
    ],
    RoomType.AUDITORIUM.value: [
        # English
        "auditorium", "hall", "assembly", "theatre", "theater", "conference",
        # Danish/Norwegian
        "aula", "forsamlingssal", "teater", "konference",
        # German
        "aula", "hörsaal", "versammlungssaal", "theater", "konferenz",
        # French
        "auditorium", "amphithéâtre", "salle_assemblée", "théâtre", "conférence",
        # Swedish
        "aula", "hörsal", "föreläsningssal", "teater", "konferens"
    ],
    RoomType.LABORATORY.value: [
        # English
        "laboratory", "lab", "research", "science", "experiment",
        # Danish/Norwegian
        "laboratorium", "lab", "forskning", "videnskab", "eksperiment",
        # German
        "labor", "laboratorium", "forschung", "wissenschaft", "experiment",
        # French
        "laboratoire", "labo", "recherche", "science", "expérience",
        # Swedish
        "laboratorium", "labb", "forskning", "vetenskap", "experiment"
    ],
    RoomType.MEETING_ROOM.value: [
        # English
        "meeting", "conference", "boardroom", "discussion", "seminar",
        # Danish/Norwegian
        "møderum", "konference", "bestyrelsesrum", "diskussion",
        # German
        "besprechung", "konferenz", "sitzungssaal", "meeting", "diskussion",
        # French
        "salle_réunion", "conférence", "conseil", "discussion", "séminaire",
        # Swedish
        "mötesrum", "konferens", "styrelserum", "diskussion"
    ],
    RoomType.CORRIDOR.value: [
        # English
        "corridor", "hallway", "passage", "entrance", "lobby",
        # Danish/Norwegian
        "gang", "korridor", "passage", "indgang", "lobby",
        # German
        "gang", "korridor", "flur", "eingang", "lobby", "durchgang",
        # French
        "couloir", "passage", "entrée", "lobby", "hall",
        # Swedish
        "korridor", "gång", "passage", "entré", "lobby"
    ],
    RoomType.OFFICE.value: [
        # English
        "office", "workspace", "desk", "administration", "staff",
        # Danish/Norwegian
        "kontor", "arbejdsplads", "skrivebord", "administration", "personale",
        # German
        "büro", "arbeitsplatz", "schreibtisch", "verwaltung", "personal",
        # French
        "bureau", "espace_travail", "administration", "personnel",
        # Swedish
        "kontor", "arbetsplats", "skrivbord", "administration", "personal"
    ]
}
