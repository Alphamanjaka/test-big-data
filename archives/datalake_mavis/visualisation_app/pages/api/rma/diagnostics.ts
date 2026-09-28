import type { NextApiRequest, NextApiResponse } from 'next'
// import rmaData from '../../../data/rma-data.json'
import { getSession } from "next-auth/react";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // const session = await getSession({ req });
  // if (!session) {
  //   return res.status(401).json({ message: "Non authentifié" });
  // }
  if (req.method === 'GET') {
     try {
        // const token = session.jwt;
        // Récupération de   l'URL depuis la variable d'environnement
        const SERVER_URL = process.env.SERVER_URL;
        if (!SERVER_URL) {
          return res.status(500).json({ success: false, message: 'URL de l’API non définie' });
        }

        // Remplacez l'URL par celle de votre API
        // const response = await fetch(`${SERVER_URL}/rma/diagnostics_heatmap`, {
        //   headers: {
        //     "Authorization": `Bearer ${token}`,
        //     "Content-Type": "application/json",
        //   },
        // });
        const response = await fetch(`${SERVER_URL}/rma/diagnostics_heatmap`);
        if (!response.ok) {
          return res.status(response.status).json({ success: false, message: 'Erreur API' });
        }
        
        const data = await response.json();
        res.status(200).json({
          success: true,
          data: data.data,
          lastSync: new Date().toISOString()
        });
      } catch (error: any) {
        res.status(500).json({ success: false, message: error.message });
      }
  } else {
    res.setHeader('Allow', ['GET'])
    res.status(405).end(`Method ${req.method} Not Allowed`)
  }
}
