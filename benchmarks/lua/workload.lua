-- Fixed allocation/sort/GC workload for C5.5.
local rounds = tonumber(arg[1]) or 20
local count = tonumber(arg[2]) or 100000
assert(math.type(rounds) == "integer" and rounds > 0, "rounds must be a positive integer")
assert(math.type(count) == "integer" and count > 0, "count must be a positive integer")

local prefix = "record:" .. string.rep("x", 64)
local checksum = 0
local function by_id(a, b)
    return a.id < b.id
end

for round = 1, rounds do
    local records = {}
    for i = count, 1, -1 do
        records[#records + 1] = {id = i, payload = prefix .. tostring(i)}
    end
    table.sort(records, by_id)
    for i = 1, count do
        local record = records[i]
        checksum = checksum + i * record.id + #record.payload
    end
    records = nil
    collectgarbage("collect")
end

print(string.format("rounds=%d objects=%d checksum=%d", rounds, count, checksum))
