const { PrismaClient } = require("@prisma/client");
const bcrypt = require("bcryptjs");

const prisma = new PrismaClient();

async function main() {
  const hashedPassword = await bcrypt.hash("dataviz", 10);

  await prisma.user.upsert({
    where: { email: "dataviz@mmt.mg" },
    update: {},
    create: {
      firstName: "ADMIN",
      lastName: "DATAVIZ",
      email: "dataviz@mmt.mg",
      password: hashedPassword,
      role: "ADMIN",
    },
  });

  await prisma.user.upsert({
    where: { email: "medecin@mmt.mg" },
    update: {},
    create: {
      firstName: "MEDECIN",
      lastName: "TEST",
      email: "medecin@mmt.mg",
      password: hashedPassword,
      role: "MEDECIN",
    },
  });

  console.log("✅ Admin + Médecin créés");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
