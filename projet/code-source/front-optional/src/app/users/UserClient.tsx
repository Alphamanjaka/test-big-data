'use client'

import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { UserRoundPen, UserRoundPlus, UserPen, UserRoundX, Contact} from 'lucide-react'
import { useEffect, useState } from 'react'

interface User {
  id: string
  firstName: string
  lastName: string
  email: string
  role: string
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [form, setForm] = useState({ firstName: '',lastName: '', email: '', role: 'user', password: '' })

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => setUsers(data))
  }, [])

  const openModal = (user?: User) => {
    if (user) {
      setEditingUser(user)
      setForm({ firstName: user.firstName,lastName: user.lastName, email: user.email, role: user.role, password: '' })
    } else {
      setEditingUser(null)
      setForm({ firstName: '',lastName: '', email: '', role: 'user', password: '' })
    }
    setModalOpen(true)
  }

  const closeModal = () => setModalOpen(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editingUser) {
      // Mise à jour
      await fetch(`/api/users/${editingUser.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      setUsers(users.map(u => (u.id === editingUser.id ? { ...u, ...form } : u)))
    } else {
      // Création
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const newUser = await res.json()
      setUsers([...users, newUser])
    }
    closeModal()
  }

  const deleteUser = async (id: string) => {
    if (!confirm('Voulez-vous vraiment supprimer cet utilisateur ?')) return
    await fetch(`/api/users/${id}`, { method: 'DELETE' })
    setUsers(users.filter(u => u.id !== id))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Contact className="w-5 h-5 text-blue-600" />
              <span>Gestion des utilisateurs</span>
            </CardTitle>
            <CardDescription>
              Liste des utilisateurs avec options d'édition et de suppression.
            </CardDescription>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="default"
              size="sm"
              onClick={() => openModal()}
            // onClick={() => handleChangeView("chart")}
            >
              <UserRoundPlus className="w-4 h-4 mr-1" /> Ajouter utilisateur
            </Button>
          </div>
        </CardHeader>
        <CardContent>

          {/* Table des utilisateurs */}
          <table className="min-w-full border border-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-2 border">Nom</th>
                <th className="p-2 border">Email</th>
                <th className="p-2 border">Rôle</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id} className="text-left">
                  <td className="p-2 border">{user.firstName+ ' '+ user.lastName}</td>
                  <td className="p-2 border">{user.email}</td>
                  <td className="p-2 border">{user.role}</td>
                  <td className="p-2 border space-x-2">
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => openModal(user)}
                      className='bg-yellow-400 rounded text-dark hover:bg-yellow-500'
                    >
                      <UserPen className="w-4 h-4 mr-1" /> Editer
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => deleteUser(user.id)}
                      className='bg-red-500 text-white hover:bg-red-600'
                    >
                      <UserRoundX className="w-4 h-4 mr-1" /> Supprimer
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>


      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow-md w-full max-w-md relative">
            <button
              className="absolute top-2 right-2 text-gray-500 hover:text-gray-800"
              onClick={closeModal}
            >
              ✖
            </button>
            <h2 className="text-xl font-bold mb-4">{editingUser ? 'Éditer un utilisateur' : 'Créer un utilisateur'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                name="firstName"
                placeholder="Nom"
                value={form.firstName}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                required
              />
              <input
                type="text"
                name="lastName"
                placeholder="Prénom"
                value={form.lastName}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                required
              />
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={form.email}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                required
              />
              <select name="role" value={form.role} onChange={handleChange} className="w-full p-2 border rounded">
                <option value="MEDECIN">Utilisateur</option>
                <option value="ADMIN">Administrateur</option>
              </select>
              {!editingUser && (
                <input
                  type="password"
                  name="password"
                  placeholder="Mot de passe"
                  value={form.password}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                  required
                />
              )}
              <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded">
                {editingUser ? 'Sauvegarder' : 'Créer'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
