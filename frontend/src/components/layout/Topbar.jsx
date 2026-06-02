import { Menu } from 'lucide-react'

export default function Topbar({ title, onMenuClick }) {
  const dateStr = new Date().toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  return (
    <header className="h-14 bg-white border-b border-[#e3e8ef] flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-3">
        <button
          className="md:hidden p-1.5 rounded-lg text-[#546e7a] hover:bg-[#f6f9fc] transition-colors"
          onClick={onMenuClick}
          aria-label="Open menu"
        >
          <Menu size={18} />
        </button>
        <h1 className="text-[15px] font-semibold text-[#0a2540] tracking-tight">
          {title}
        </h1>
      </div>
      <span className="text-[13px] text-[#94a3b8] font-mono hidden sm:block">
        {dateStr}
      </span>
    </header>
  )
}
