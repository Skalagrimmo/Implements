local ReactionSystem = {}
ReactionSystem.__index = ReactionSystem

function ReactionSystem.new(rules)
  local copy = {}
  for i = 1, #(rules or {}) do copy[i] = rules[i] end
  return setmetatable({ rules = copy }, ReactionSystem)
end

function ReactionSystem:react(ctx)
  local reactions = {}
  for i = 1, #self.rules do
    local rule = self.rules[i]
    if rule.matches(ctx) then
      local produced = rule.apply(ctx)
      if produced ~= nil then
        if type(produced) == "table" and produced.type == nil and #produced > 0 then
          for j = 1, #produced do reactions[#reactions + 1] = produced[j] end
        else
          reactions[#reactions + 1] = produced
        end
      end
    end
  end
  return reactions
end

return ReactionSystem
