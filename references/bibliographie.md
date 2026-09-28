# Bibliographie

> Sources citées dans le mémoire. Vérifiées le 08/09/2026 (B1 à B12) et le 27/09/2026
> (B13 à B20, étude de l'existant). Les références sont
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
- **[B4]** RapidFuzz — documentation et source (v3.14.5).
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
  https://moj-analytical-services.github.io/splink
- **[B16]** HAPI FHIR — implémentation open source (Java, Apache 2.0) de la spécification
  FHIR : serveurs Plain / JPA / JAX-RS, opérations REST, recherche, `$match`.
  https://hapifhir.io/ ; https://github.com/hapifhir/hapi-fhir
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