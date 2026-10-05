local palette = require("render.palette")
local LoveRenderer = {}
LoveRenderer.__index = LoveRenderer

local function setc(c, alpha)
  love.graphics.setColor(c[1], c[2], c[3], alpha or c[4] or 1)
end

function LoveRenderer.new(opts)
  opts = opts or {}
  return setmetatable({
    scale = opts.scale or 3,
    logical_w = opts.logical_w or 320,
    logical_h = opts.logical_h or 180,
  }, LoveRenderer)
end

function LoveRenderer:begin_frame(world)
  setc(palette.ink)
  love.graphics.clear(palette.ink)
  love.graphics.push("all")
  love.graphics.scale(self.scale, self.scale)
  love.graphics.setDefaultFilter("nearest", "nearest")
end

function LoveRenderer:draw_tile(tile, x, y, size)
  local c = palette[tile] or palette.earth
  setc(c)
  love.graphics.rectangle("fill", x, y, size, size)
  if tile == "water" then
    setc(palette.ice, 0.25)
    love.graphics.line(x + 2, y + size * 0.55, x + size - 2, y + size * 0.55)
  elseif tile == "path" then
    setc(palette.cream, 0.12)
    love.graphics.rectangle("fill", x + 2, y + 2, 2, 2)
  end
end

function LoveRenderer:draw_entity(entity)
  local x, y = entity.x, entity.y
  setc(palette.shadow)
  love.graphics.ellipse("fill", x, y + 5, 5, 2)
  local c = palette[entity.color or "gold"] or palette.gold
  setc(c)
  love.graphics.rectangle("fill", x - 3, y - 7, 7, 9)
  setc(palette.cream)
  love.graphics.rectangle("fill", x - 2, y - 10, 5, 4)
  setc(palette.ink)
  love.graphics.points(x - 1, y - 9, x + 1, y - 9)
  setc(palette.cream)
  love.graphics.print(entity.name or entity.id, math.floor(x - 10), math.floor(y + 8), 0, 0.35, 0.35)
end

function LoveRenderer:draw_event(event)
  if not event.location then return end
  local x, y = event.location.x, event.location.y
  if event.type == "freeze" then
    setc(palette.ice, 0.85)
  elseif event.type == "burn" then
    setc(palette.fire, 0.9)
  else
    setc(palette.gold, 0.9)
  end
  love.graphics.circle("line", x, y, 8)
end

function LoveRenderer:draw_hud(info)
  setc(palette.ink, 0.82)
  love.graphics.rectangle("fill", 4, 4, 312, 30)
  setc(palette.cream)
  love.graphics.print("EBE / LÖVE2D — hour " .. tostring(info.hour), 8, 7, 0, 0.55, 0.55)
  love.graphics.print("1 freeze   2 burn   3 craft   SPACE +1h   R reset", 8, 18, 0, 0.42, 0.42)
  love.graphics.print(info.message or "", 8, 164, 0, 0.42, 0.42)
end

function LoveRenderer:end_frame(world)
  love.graphics.pop()
end

return LoveRenderer
