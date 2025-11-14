import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Spatial Entity & Sensor Flow Editor',
  description: 'Visual editor for defining spatial entities and sensors',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
