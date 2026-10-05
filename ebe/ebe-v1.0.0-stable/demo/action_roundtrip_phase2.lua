local root=arg[1]
local snapshot_path=arg[2]
local bundle_path=arg[3]
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local snapshot=EBE.Snapshot.read_lua(snapshot_path)
local rt=EBE.Runtime.restore(snapshot)
local pending=rt:action_requests("exported","pixelgen_world_event")
assert(#pending==1,"expected one exported request before feedback")
local id=pending[1].id
local bundle=EBE.PixelGenV080.load_file(bundle_path)
local imported=rt:ingest_pixelgen(bundle)
assert(imported.action_results==1,"PixelGen feedback did not resolve action")
local req=rt:action_request(id)
assert(req.status=="applied","request not applied")
print("action_id="..id)
print("status="..req.status)
print("derived_event_id="..tostring(req.result.derived_event_id))
print("revision="..tostring(req.result.revision))
