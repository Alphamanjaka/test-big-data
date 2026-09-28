# Bibliographie

> Sources citées dans le mémoire. Vérifiées le 08/09/2026 (B1 à B12), le 27/09/2026
> (B13 à B20, étude de l'existant) et le 28/09/2026 (B21 à B31, compléments de l'état de l'art ;
> compléments de B4, B15 et B16). Les références sont
> indexées sous la forme `[B#]` dans le texte des chapitres.

## Entity Resolution / Record Linking

- **[B1]** ELMAGARMID, Ahmed K. ; IPEIROTIS, Panagiotis G. ; VERYKIOS, Vassilios S.
  *Duplicate Record Detection: A Survey*. IEEE Transactions on Knowledge and Data
  Engineering, vol. 19, n° 1, 2007, p. 1-16.
  https://www.cs.purdue.edu/homes/ake/pub/survey2.pdf
- **[B2]** FELLEGI, Ivan P. ; SUNTER, Alan B.
  *A Theory for Record Linkage*. Journal of the American Statistical Association,
  vol. 64, n° 328, 1969, p. 1183-1210. doi:10.2307/2286061
- **[B3]** CHRISTEN, Peter.
  *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution,
  and Duplicate Detection*. Springer, Data-Centric Systems and Applications, 2012.
  doi:10.1007/978-3-642-31164-2
- **[B4]** RapidFuzz — documentation et source (documentation consultée : v3.14.5, qui exige
  Python ≥ 3.10 ; sous Python 3.8, dernière version installable : 3.9.7, voir [B31]).
  https://rapidfuzz.github.io/RapidFuzz/ ; https://github.com/rapidfuzz/RapidFuzz

## Standards de santé et interopérabilité

- **[B5]** HL7 FHIR, specification Resource Patient (v5.0.0) — dont le service de
  Master Patient Index `$match` (§8.1.11). https://www.hl7.org/fhir/patient.html

## Architecture Big Data

- **[B6]** Apache Hadoop — HDFS (architecture NameNode / DataNodes).
  https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html
- **[B7]** Apache Spark — Unified Analytics Engine. https://spark.apache.org
- **[B8]** Apache Hive — SQL sur Hadoop (HiveServer2, metastore).
  https://hive.apache.org
- **[B9]** Databricks — documentation « Lakehouse Medallion Architecture ».
  https://docs.databricks.com/aws/en/lakehouse/medallion

## Réglementation et protection des données de santé

- **[B10]** Règlement (UE) 2016/679 (RGPD), article 9 — « Traitement portant sur des
  catégories particulières de données à caractère personnel ».
- **[B11]** CNIL — « Quelles formalités pour les traitements de données de santé ? »
  (article 9 du RGPD ; article 6 et 44 de la loi Informatique et Libertés).
  https://www.cnil.fr/fr/quelles-formalites-pour-les-traitements-de-donnees-de-sante
- **[B12]** CNIL — « RGPD et professionnels de santé libéraux : ce que vous devez
  savoir ». https://www.cnil.fr/fr/rgpd-et-professionnels-de-sante-liberaux-ce-que-vous-devez-savoir

## Solutions existantes (état de l'art, § 2.2 à 2.4)

> Étude **documentaire** : aucun de ces produits n'a été installé ni exécuté dans le projet. Les
> capacités citées sont celles **annoncées** par leur documentation. Sources vérifiées le 27/09/2026.

- **[B13]** INTERSYSTEMS — *InterSystems EMPI* (Enterprise Master Person Index) et
  documentation *IRIS for Health* : services IHE **PIXv3** (MRN + assigning authority → MPI ID)
  et **PDQv3** (démographiques partiels → MPI IDs), modes de rapprochement
  *Probable* / *Strict* / *Never*, composite record, *referential matching*.
  https://www.intersystems.com/products/intersystems-empi/ ;
  https://docs.intersystems.com/irisforhealthlatest/
- **[B14]** QLIK — Talend MDM, *Integrated Matching* : *match and survivorship*,
  *golden record*, tâches de fusion validées par des data stewards, seuil de confiance.
  https://help.qlik.com/talend/en-US/mdm-examples/8.0/integrated-matching-in-talend-mdm
- **[B15]** LINACRE, Robin ; LINDSAY, Sam ; MANASSIS, Theodore ; SLADE, Zoe ; HEPWORTH, Tom ;
  KENNEDY, Ross ; BOND, Andrew. *Splink: Free software for probabilistic record linkage at
  scale*. International Journal of Population Data Science, vol. 7, n° 3, 2022.
  doi:10.23889/ijpds.v7i3.1794 — https://ijpds.org/article/view/1794 ;
  https://moj-analytical-services.github.io/splink ; graphique « en cascade » (contribution de
  chaque comparaison au score) : https://moj-analytical-services.github.io/splink/charts/waterfall_chart.html
  (consulté le 28/09/2026)
- **[B16]** HAPI FHIR — implémentation open source (Java, Apache 2.0) de la spécification
  FHIR : serveurs Plain / JPA / JAX-RS, opérations REST, recherche, `$match`.
  https://hapifhir.io/ ; https://github.com/hapifhir/hapi-fhir ; intercepteur de consentement
  (cadre à programmer, « not a complete working solution ») :
  https://hapifhir.io/hapi-fhir/docs/security/consent_interceptor.html (consulté le 28/09/2026)
- **[B17]** Microsoft — *Azure Health Data Services* : services FHIR et DICOM, export
  `$export` vers Data Lake Storage Gen2, service de dé-identification (27 entités, opérations
  `TAG` / `REDACT` / `SURROGATE`).
  https://learn.microsoft.com/en-us/azure/healthcare-apis/fhir/export-data ;
  https://learn.microsoft.com/en-us/azure/healthcare-apis/deidentification/overview
- **[B18]** Apache Atlas — *Data Governance and Metadata framework for Hadoop* : catalogue,
  lineage, classifications `PII` / `SENSITIVE` propagées le long des traitements.
  https://atlas.apache.org/
- **[B19]** GNU Health — écosystème libre de santé (EMR, HMIS, HIS, LISM ; GPL v3+),
  socle des tables `gnuhealth_patient` / `party_party` / `gnuhealth_family` exploitées par la
  source `MMT_DB`. https://www.gnuhealth.org ; https://docs.gnuhealth.org
- **[B20]** Odoo — ERP open source (AGPL-3) et applications hospitalières tierces (licences
  OPL-1 / propriétaire), socle des tables `hms_*` / `res_*` de la source `MAVIS`.
  https://www.odoo.com ; https://apps.odoo.com/apps/modules/19.0/base_hospital_management

## Compléments de l'état de l'art (§ 2.1 et § 2.2)

> Sources consultées le 28/09/2026. Les publications scientifiques sont citées par leur DOI ; les
> pages web par leur URL. Les bibliothèques n'ont été ni installées ni exécutées : leur
> compatibilité est lue dans les métadonnées officielles de leurs versions [B31].

- **[B21]** LI, Yuliang ; LI, Jinfeng ; SUHARA, Yoshihiko ; DOAN, AnHai ; TAN, Wang-Chiew.
  *Deep Entity Matching with Pre-Trained Language Models* (Ditto). Proceedings of the VLDB
  Endowment, vol. 14, n° 1, 2020, p. 50-60. doi:10.14778/3421424.3421431 —
  https://www.vldb.org/pvldb/vol14/p50-li.pdf
- **[B22]** PEETERS, Ralph ; STEINER, Aaron ; BIZER, Christian. *Entity Matching using Large
  Language Models*. Proceedings of the 28th International Conference on Extending Database
  Technology (EDBT 2025), p. 529-541.
  https://www.uni-mannheim.de/media/Einrichtungen/dws/DWS_News/Documents/Peeters-Entity-Matching-using-LLMs-EDBT2025.pdf
- **[B23]** SCHNELL, Rainer ; BACHTELER, Tobias ; REIHER, Jörg. *Privacy-preserving record
  linkage using Bloom filters*. BMC Medical Informatics and Decision Making, vol. 9, art. 41,
  2009. doi:10.1186/1472-6947-9-41 — https://pmc.ncbi.nlm.nih.gov/articles/PMC2753305/

### Cadre juridique malgache

- **[B24]** RÉPUBLIQUE DE MADAGASCAR. *Loi n° 2014-038 du 9 janvier 2015 sur la protection des
  données à caractère personnel* — art. 13 (consentement), 14 (finalités), 15 (sécurité),
  17 (légitimation), 18 (données sensibles, dont la santé), 20 (transfert à l'étranger),
  28 (création de la CMIL), 43 (déclaration ou registre), 46 (autorisation préalable).
  https://www.afapdp.org/wp-content/uploads/2018/05/Madagascar-L-2014-038-du-09-01-15-sur-la-protection-des-donnees-a-caractere-personnel.pdf ;
  https://digital.gov.mg/en/2022/07/05/loi-n-2014-038-sur-la-protection-des-donnees-a-caractere-personnel/
- **[B25]** LAW LAB AFRICA. *Data Protection in Madagascar: Law, Regulator, Enforcement* — CMIL
  « being operationalized », non opérationnelle ; décret d'application n° 2023-1541 ; aucune
  décision de contrôle publiée. Source secondaire (observatoire indépendant).
  https://research.lawlab.africa/madagascar/

### Standards et architectures

- **[B26]** HL7 FHIR, specification *Resource Consent* (v5.0.0) : décision *permit* / *deny*,
  *provisions*, `provision.purpose` (vocabulaire *PurposeOfUse*) ; maturité 2 (*Trial Use*) ;
  application du consentement hors du périmètre de la spécification.
  https://hl7.org/fhir/consent.html
- **[B27]** ARMBRUST, Michael ; GHODSI, Ali ; XIN, Reynold ; ZAHARIA, Matei. *Lakehouse: A New
  Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics*. CIDR 2021.
  https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf
- **[B28]** ARMBRUST, Michael ; DAS, Tathagata ; et al. *Delta Lake: High-Performance ACID
  Table Storage over Cloud Object Stores*. Proceedings of the VLDB Endowment, vol. 13, n° 12,
  2020, p. 3411-3424. doi:10.14778/3415478.3415560 — compatibilité Delta 2.4.x / Spark 3.4.x :
  https://docs.delta.io/latest/releases.html

### Produits et dépendance aux éditeurs

- **[B29]** INTRAHEALTH INTERNATIONAL — *OpenCR* (Open Client Registry), registre de clients
  open source de l'écosystème OpenHIE : règles de décision déterministes et probabilistes,
  revue humaine, FHIR R4 ; pile Node.js, HAPI FHIR et Elasticsearch.
  https://intrahealth.github.io/client-registry/ ; https://github.com/intrahealth/client-registry
- **[B30]** QLIK — *Talend Open Studio* : « As of January 31, 2024, the open-source version of
  Talend Studio was retired and is no longer hosted or updated by Qlik and Talend ».
  https://www.qlik.com/us/products/talend-open-studio

### Métadonnées des bibliothèques

- **[B31]** PYTHON PACKAGE INDEX (PyPI) — champ `Requires-Python` des versions publiées,
  consulté le 28/09/2026 : Splink 4.0.11 (12/11/2025) dernière version pour Python ≥ 3.8,
  Splink 5.0.0 (28/09/2026) exige ≥ 3.10 ; recordlinkage 0.16 (20/07/2023, ≥ 3.8) ;
  dedupe 3.0.3 (15/08/2024, ≥ 3.8) ; DuckDB 1.2.2 et Polars 1.9.0 dernières versions publiées pour
  Python 3.8 ; RapidFuzz 3.9.7 (02/09/2024) dernière version pour Python 3.8 ; delta-spark 2.4.0
  (≥ 3.6). https://pypi.org/pypi/<paquet>/json
