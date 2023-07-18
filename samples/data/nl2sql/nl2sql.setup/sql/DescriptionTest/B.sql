-- Table and column identities devoid of meaning
create table B (
  B0 INT PRIMARY KEY,
  B1 VARCHAR(50),
  B2 BIT
);

-- Descriptions captured as extened-properties
EXEC sys.sp_addextendedproperty 
@name  = N'MS_Description', @value = N'Interest Categories', 
@level0type = N'SCHEMA', @level0name = N'dbo', 
@level1type = N'TABLE', @level1name = B;
EXEC sys.sp_addextendedproperty 
@name  = N'MS_Description', @value = N'Unique identifier for categories', 
@level0type = N'SCHEMA', @level0name = N'dbo', 
@level1type = N'TABLE', @level1name = B,
@level2type = N'COLUMN', @level2name = B0;
EXEC sys.sp_addextendedproperty 
@name  = N'MS_Description', @value = N'The category name', 
@level0type = N'SCHEMA', @level0name = N'dbo', 
@level1type = N'TABLE', @level1name = B,
@level2type = N'COLUMN', @level2name = B1;
EXEC sys.sp_addextendedproperty 
@name  = N'MS_Description', @value = N'Flag indicating if categories as active/enabled.', 
@level0type = N'SCHEMA', @level0name = N'dbo', 
@level1type = N'TABLE', @level1name = B,
@level2type = N'COLUMN', @level2name = B2;

-- Sample data
insert into B (B0, B1, B2) values (1, 'Food', 0);
insert into B (B0, B1, B2) values (2, 'Toys', 0);
insert into B (B0, B1, B2) values (3, 'Clothing', 0);
insert into B (B0, B1, B2) values (4, 'Baby', 0);
insert into B (B0, B1, B2) values (5, 'Automotive', 0);
insert into B (B0, B1, B2) values (6, 'Games', 0);
insert into B (B0, B1, B2) values (7, 'Music', 1);
insert into B (B0, B1, B2) values (8, 'Sports', 0);
insert into B (B0, B1, B2) values (9, 'Fitness', 1);
insert into B (B0, B1, B2) values (10, 'Music', 1);
insert into B (B0, B1, B2) values (11, 'Pizza', 1);
insert into B (B0, B1, B2) values (12, 'Shoes', 0);
insert into B (B0, B1, B2) values (13, 'Tools', 1);
insert into B (B0, B1, B2) values (14, 'Entertainment', 1);
insert into B (B0, B1, B2) values (15, 'Automotive', 1);
insert into B (B0, B1, B2) values (16, 'Computers', 0);
insert into B (B0, B1, B2) values (17, 'Health', 1);
insert into B (B0, B1, B2) values (18, 'Travel', 1);
insert into B (B0, B1, B2) values (19, 'Garden', 0);
insert into B (B0, B1, B2) values (20, 'Kids', 0);
