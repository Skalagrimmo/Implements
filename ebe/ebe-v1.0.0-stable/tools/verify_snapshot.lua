local root=arg[1] or "."
local path=arg[2]
local format=arg[3] or "json"
if not path then
  io.stderr:write("usage: texlua tools/verify_snapshot.lua <ebe-root> <snapshot-path> [json|lua]\n")
  os.exit(2)
end
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local raw
if format=="json" then raw=EBE.Snapshot.read_json(path)
elseif format=="lua" then raw=EBE.Snapshot.read_lua(path)
else error("format must be json or lua") end
local migrated=EBE.PersistenceContract.migrate_snapshot(raw)
EBE.PersistenceContract.assert_snapshot(migrated)
print("EBE snapshot: PASS")
print("source_version="..tostring(raw.version))
print("runtime_version="..tostring(migrated.version))
print("contract_version="..tostring(migrated.contract_version))
print("snapshot_hash="..EBE.Snapshot.hash(migrated))
