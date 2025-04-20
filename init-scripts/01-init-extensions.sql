-- Install and enable the vector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Install and enable the AGE extension for graph operations
CREATE EXTENSION IF NOT EXISTS age;

-- Verify that extensions are installed
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'age');

-- Create a verification function
CREATE OR REPLACE FUNCTION check_extensions() RETURNS TABLE (name text, installed boolean) AS $$
BEGIN
    RETURN QUERY
    SELECT 'vector'::text, EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') AS installed
    UNION ALL
    SELECT 'age'::text, EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'age') AS installed;
END;
$$ LANGUAGE plpgsql;

-- Call it to see the results
SELECT * FROM check_extensions();

--------------------------
-- Initialize AGE Graph DB
--------------------------

-- Load the AGE module
LOAD 'age';

-- Set the search path to include ag_catalog
SET search_path = ag_catalog, embediq, public;

-- Check if embediq_graph exists and create it if it doesn't
DO $$
DECLARE
    graph_exists BOOLEAN;
    graph_name TEXT := 'embediq_graph';
BEGIN
    SELECT EXISTS(SELECT 1 FROM ag_graph WHERE name = graph_name) INTO graph_exists;
    
    IF NOT graph_exists THEN
        RAISE NOTICE 'Creating AGE graph %', graph_name;
        PERFORM create_graph(graph_name);
        RAISE NOTICE '✓ Graph created successfully';
    ELSE
        RAISE NOTICE 'Graph % already exists', graph_name;
    END IF;
END $$;

-- Verify the graph exists
SELECT * FROM ag_graph; 