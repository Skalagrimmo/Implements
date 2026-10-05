local Renderer = require("render.renderer")
local LoveRenderer = require("render.love_renderer")
local Game = require("demo.game")

local game
local renderer

function love.load()
  love.graphics.setDefaultFilter("nearest", "nearest")
  game = Game.new()
  renderer = Renderer.new(LoveRenderer.new({ scale = 3, logical_w = 320, logical_h = 180 }))
end

function love.keypressed(key)
  if key == "1" then game:emit_freeze()
  elseif key == "2" then game:emit_burn()
  elseif key == "3" then game:emit_craft()
  elseif key == "space" then game:advance_hour()
  elseif key == "r" then game:reset()
  elseif key == "escape" then love.event.quit() end
end

function love.draw()
  renderer:begin_frame(game.world)
  local ts = game.world.tile_size
  for ty = 1, game.world.height do
    for tx = 1, game.world.width do
      renderer:draw_tile(game.world.tile_at(tx, ty), (tx - 1) * ts, (ty - 1) * ts, ts)
    end
  end

  for i = 1, #game.engine.history do renderer:draw_event(game.engine.history[i]) end
  for i = 1, #game.world.observers do renderer:draw_entity(game.world.observers[i]) end

  local tail = game.message
  local o = game.world.observers[1]
  local summary = game:knowledge_summary(o)
  if summary ~= "" then tail = tail .. "  Mira: " .. summary end
  renderer:draw_hud({ hour = math.floor(game.engine.clock:now()), message = tail })
  renderer:end_frame(game.world)
end
