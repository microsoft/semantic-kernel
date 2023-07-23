-- Manually create server login:
-- CREATE LOGIN search_bot ...

-- Create the database role
CREATE ROLE bot_reader AUTHORIZATION [dbo]
GO

-- Create user linked to login
CREATE USER search_bot
	FOR LOGIN search_bot
	WITH DEFAULT_SCHEMA = [SalesLT]
GO

-- Add an existing user to the role
EXEC sp_addrolemember N'bot_reader', N'search_bot'
GO

-- https://learn.microsoft.com/en-us/previous-versions/sql/sql-server-2008-r2/ms175808(v=sql.105)
DENY VIEW DEFINITION to bot_reader
GO
REVOKE VIEW DEFINITION to bot_reader
GO
DENY SELECT ON SCHEMA::[sys] TO bot_reader
GO
DENY SELECT ON SCHEMA::[INFORMATION_SCHEMA] TO bot_reader
GO
REVOKE SELECT TO bot_reader
GO
DENY SELECT ON SCHEMA::[sys] TO bot_reader
GO
DENY SELECT ON SCHEMA::[INFORMATION_SCHEMA] TO bot_reader
GO

-- Grant access rights to a specific schema, tables, or views
GRANT SELECT ON SCHEMA::[SalesLT] TO bot_reader
GO




 
