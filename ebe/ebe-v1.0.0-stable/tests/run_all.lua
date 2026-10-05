local root=arg[1] or "."
local tests={
  "tests/package_api.lua",
  "tests/test_core.lua",
  "tests/test_pixelgen_bridge.lua",
  "tests/test_pixelgen_v100_compat.lua",
  "tests/test_distortion.lua",
  "tests/test_information_ecology.lua",
  "tests/test_network_synthesis.lua",
  "tests/test_collective_epistemics.lua",
  "tests/test_institutional_policy.lua",
  "tests/test_action_requests.lua",
  "tests/test_persistence_contract.lua",
  "tests/test_v100_promotion.lua",
}
for _,path in ipairs(tests) do
  local chunk=assert(loadfile(root.."/"..path))
  chunk(root)
end
print("EBE v1.0.0 all tests: PASS")
