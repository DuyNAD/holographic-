import { useState, type ReactNode } from 'react'

type PanelId = 'add' | 'guide'

interface HudMenuProps {
  selectedName: string | null
  onDelete: () => void
  addPanel: ReactNode
  guidePanel: ReactNode
}

const panelTitles: Record<PanelId, string> = {
  add: 'Thêm vật thể',
  guide: 'Hướng dẫn',
}

export default function HudMenu({
  selectedName,
  onDelete,
  addPanel,
  guidePanel,
}: HudMenuProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [panel, setPanel] = useState<PanelId | null>(null)

  const togglePanel = (id: PanelId) =>
    setPanel((current) => (current === id ? null : id))

  return (
    <nav
      className={`hud-menu ${collapsed ? 'is-collapsed' : ''}`}
      aria-label="Menu chính"
      data-hud
    >
      <div className="hud-dock hud-glass">
        <button
          className="hud-dock-button hud-dock-toggle"
          type="button"
          aria-expanded={!collapsed}
          aria-label={collapsed ? 'Mở menu' : 'Thu gọn menu'}
          data-gesture-target
          onClick={() => {
            setCollapsed((value) => !value)
            setPanel(null)
          }}
        >
          <span className="hud-icon" aria-hidden="true">
            {collapsed ? '☰' : '‹'}
          </span>
          <span className="hud-label" aria-hidden="true">
            {collapsed ? 'Menu' : 'Thu gọn'}
          </span>
        </button>

        {!collapsed && (
          <>
            <button
              className="hud-dock-button"
              type="button"
              aria-pressed={panel === 'add'}
              aria-label="Thêm vật thể"
              data-gesture-target
              onClick={() => togglePanel('add')}
            >
              <span className="hud-icon" aria-hidden="true">＋</span>
              <span className="hud-label" aria-hidden="true">Thêm</span>
            </button>
            <button
              className="hud-dock-button hud-dock-button--danger"
              type="button"
              aria-label="Xóa vật thể"
              title={
                selectedName
                  ? `Xóa “${selectedName}”`
                  : 'Chọn một vật thể để xóa'
              }
              disabled={!selectedName}
              data-gesture-target
              onClick={onDelete}
            >
              <span className="hud-icon" aria-hidden="true">✕</span>
              <span className="hud-label" aria-hidden="true">Xóa</span>
            </button>
            <button
              className="hud-dock-button"
              type="button"
              aria-pressed={panel === 'guide'}
              aria-label="Hướng dẫn"
              data-gesture-target
              onClick={() => togglePanel('guide')}
            >
              <span className="hud-icon" aria-hidden="true">?</span>
              <span className="hud-label" aria-hidden="true">Hướng dẫn</span>
            </button>
          </>
        )}
      </div>

      {!collapsed && panel && (
        <section className="hud-panel hud-glass" aria-labelledby="hud-panel-title">
          <header className="hud-panel-header">
            <h2 id="hud-panel-title">{panelTitles[panel]}</h2>
            <button
              className="hud-close"
              type="button"
              aria-label="Đóng bảng"
              data-gesture-target
              onClick={() => setPanel(null)}
            >
              ✕
            </button>
          </header>
          <div className="hud-panel-body">
            {panel === 'add' ? addPanel : guidePanel}
          </div>
        </section>
      )}
    </nav>
  )
}
