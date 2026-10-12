function enrich_docker_log(tag, timestamp, record)
    -- Prefer the container ID extracted by the Tail input's Tag_Regex.
    local container_id = tag:match("docker%.([0-9a-f]+)")

    -- Fall back to the source path if available.
    if not container_id then
        local source_file = record["source_file"] or ""
        container_id = source_file:match("/containers/([0-9a-f]+)/")
    end

    record["container_id"] = container_id or "unknown"
    record["application"] = record["application"] or "kbr"

    return 1, timestamp, record
end
