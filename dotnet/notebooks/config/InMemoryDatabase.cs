// Copyright (c) Microsoft. All rights reserved.

//Simulating a data set of security alerts by creating an in-memory SQLite database.
//We populate it with synthetic data, and printing a few example rows

// Imports
using System.Data.SQLite;
using System.Collections.Generic;
using System.Data;

// Create an in-memory (stored in RAM) SQLite database
var connectionString = "Data Source=:memory:;Version=3;New=True;";
var rand = new Random();

// Defines Supporting Data:
var titles = new string[] {
    "Ransomware-linked Sangria Tempest threat activity group detected on one endpoint",
    "A file or network connection related to a ransomware-linked emerging threat activity group detected including Ransomware on one endpoint",
    "Periwinkle Tempest activity group including Ransomware on one endpoint",
    "Lace Tempest activity group including Ransomware on one endpoint",
    "Midnight Blizzard activity group on one endpoint",
    "Emerging threat activity group Storm-0335 detected on one endpoint",
    "Storm-0904 activity group including Ransomware on one endpoint",
    "Storm-0555 activity group on one endpoint",
    "Velvet Tempest ransomware-linked activity group detected including Ransomware on one endpoint",
    "Malware associated with Hazel Sandstorm activity group on one endpoint",
    "Pink Sandstorm Activity Group on one endpoint",
    "Malware from emerging threat activity group on one endpoint",
    "A file or network connection related to a ransomware-linked emerging threat activity group detected including Ransomware",
    "Exfiltration incident involving one user",
    "Multi-stage incident involving Initial access & Credential access involving multiple users",
    "Exfiltration incident involving multiple users",
    "Initial access incident involving one user",
    "Atypical travel involving one user",
    "User account compromise identified from a known attack pattern (attack disruption)",
    "Multi-stage incident on one endpoint",
    "Initial access incident on multiple endpoints reported by multiple sources",
    "Exfiltration incident on one endpoint",
    "Login from other than GB on one endpoint",
    "Suspicious activity incident",
    "Insane malicious URL-click involving one user",
    "Lateral movement incident involving one user",
    "Multi-stage incident including Ransomware on multiple endpoints reported by multiple sources",
    "Initial access incident on one endpoint",
    "Multi-stage incident involving Initial access & Discovery involving multiple users reported by multiple sources",
    "Multiple failed user log on attempts to an app involving one user",
    "Eliminaron un objeto en Sharepoint",
    "Multiple failed user logon attempts to a service involving one user",
    "Or - CD test on one endpoint",
    "POL-CA-SP-ProdBlockDownloadsM365onunmanaged-devices involving one user",
    "Authentication from known malicious IP using compromised credentials (attack disruption)"
};

// Helper methods to generate random data
string GenerateUUID() => Guid.NewGuid().ToString();
string GenerateHexID(int length) {
    var hex = Guid.NewGuid().ToString("N"); // 32 chars
    return hex.Substring(0, Math.Min(length, hex.Length));
}

// Open connection and keep it global
var conn = new SQLiteConnection(connectionString);
conn.Open();

// Create data bese schema// Create table
var createCmd = conn.CreateCommand();
createCmd.CommandText = @"
    CREATE TABLE Alerts (
        OrgId TEXT,
        AlertId TEXT,
        IncidentId INTEGER,
        IsManual BOOLEAN,
        Time TEXT,
        IsNewIncident BOOLEAN,
        CorrelationId TEXT,
        IsInternal BOOLEAN,
        IsMtpEnabled BOOLEAN,
        IsTestTenant BOOLEAN,
        TenantId TEXT,
        IncidentTitle TEXT,
        IncidentSeverity TEXT
    );
";
createCmd.ExecuteNonQuery();

// Insert sample data to 100 rows
string[] severities = new[] { "Low", "Medium", "High" };
for (int i = 0; i < 100; i++)
{
    var insertCmd = conn.CreateCommand();
    insertCmd.CommandText = @"
        INSERT INTO Alerts (
            OrgId, AlertId, IncidentId, IsManual, Time, IsNewIncident, CorrelationId,
            IsInternal, IsMtpEnabled, IsTestTenant, TenantId, IncidentTitle, IncidentSeverity
        ) VALUES (
            @OrgId, @AlertId, @IncidentId, @IsManual, @Time, @IsNewIncident, @CorrelationId,
            @IsInternal, @IsMtpEnabled, @IsTestTenant, @TenantId, @IncidentTitle, @IncidentSeverity
        );";

    insertCmd.Parameters.AddWithValue("@OrgId", GenerateUUID());
    insertCmd.Parameters.AddWithValue("@AlertId", GenerateHexID(24));
    insertCmd.Parameters.AddWithValue("@IncidentId", rand.Next(10000, 999999));
    insertCmd.Parameters.AddWithValue("@IsManual", rand.Next(0, 2) == 1);
    insertCmd.Parameters.AddWithValue("@Time", DateTime.UtcNow.ToString("o") + "Z");
    insertCmd.Parameters.AddWithValue("@IsNewIncident", rand.Next(0, 2) == 1);
    insertCmd.Parameters.AddWithValue("@CorrelationId", "");
    insertCmd.Parameters.AddWithValue("@IsInternal", rand.Next(0, 2) == 1);
    insertCmd.Parameters.AddWithValue("@IsMtpEnabled", true);
    insertCmd.Parameters.AddWithValue("@IsTestTenant", false);
    insertCmd.Parameters.AddWithValue("@TenantId", "StrPII_" + GenerateHexID(40));
    insertCmd.Parameters.AddWithValue("@IncidentTitle", titles[rand.Next(titles.Length)]);
    insertCmd.Parameters.AddWithValue("@IncidentSeverity", severities[rand.Next(severities.Length)]);

    insertCmd.ExecuteNonQuery();
}

DataTable RunQueryToDataTable(string sqlQuery, SQLiteConnection conn)
{
    var dataTable = new DataTable();

    using (var cmd = conn.CreateCommand())
    {
        cmd.CommandText = sqlQuery;
        using (var adapter = new SQLiteDataAdapter(cmd))
        {
            adapter.Fill(dataTable);
        }
    }
    return dataTable;
}