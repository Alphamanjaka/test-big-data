-- Renommage du rôle DOCTOR en MEDECIN (alignement cahier des charges / MODULE_2)
ALTER TYPE "public"."Role" RENAME VALUE 'DOCTOR' TO 'MEDECIN';

ALTER TABLE "public"."User" ALTER COLUMN "role" SET DEFAULT 'MEDECIN';
