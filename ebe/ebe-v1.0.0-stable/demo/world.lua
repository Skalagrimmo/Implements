local World = {}

World.tile_size = 16
World.width = 20
World.height = 12

World.observers = {
  { id = "mira", name = "Mira", x = 68,  y = 100, group = "keepers", color = "gold",   values = { nature = 1.0, harm = -0.8, lore = 0.2, trade = 0.1, cunning = 0.1 } },
  { id = "oren", name = "Oren", x = 144, y = 86,  group = "traders", color = "berry",  values = { nature = 0.1, harm = -0.1, lore = 0.2, trade = 1.0, cunning = 0.4 } },
  { id = "sava", name = "Sava", x = 230, y = 104, group = "choir",   color = "violet", values = { nature = 0.6, harm = -0.5, lore = 1.0, trade = 0.1, cunning = 0.2 } },
  { id = "tor",  name = "Tor",  x = 286, y = 88,  group = "hunters", color = "fire",   values = { nature = -0.1, harm = 0.5, lore = 0.1, trade = 0.2, cunning = 0.7 } },
}

function World.tile_at(tx, ty)
  if ty == 7 and tx >= 1 and tx <= 20 then return "path" end
  if tx >= 3 and tx <= 6 and ty >= 4 and ty <= 6 then return "water" end
  if (tx + ty) % 7 == 0 then return "grass2" end
  return "grass"
end

return World
