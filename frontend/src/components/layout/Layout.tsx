import { ReactNode } from 'react'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="h-screen flex flex-col">
      <Navbar />
      <Sidebar />
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  )
}
