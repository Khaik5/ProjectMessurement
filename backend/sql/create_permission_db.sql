IF DB_ID('PermissionDB') IS NULL
BEGIN
    CREATE DATABASE PermissionDB;
END
GO

USE PermissionDB;
GO

IF OBJECT_ID('dbo.Users', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(100) UNIQUE NOT NULL,
        FullName NVARCHAR(255) NULL,
        Email NVARCHAR(255) UNIQUE NULL,
        PasswordHash NVARCHAR(255) NOT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

IF OBJECT_ID('dbo.Roles', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Roles (
        RoleID INT IDENTITY(1,1) PRIMARY KEY,
        RoleCode NVARCHAR(50) UNIQUE NOT NULL,
        RoleName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

IF OBJECT_ID('dbo.UserRoles', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.UserRoles (
        UserID INT NOT NULL,
        RoleID INT NOT NULL,
        PRIMARY KEY (UserID, RoleID),
        CONSTRAINT FK_UserRoles_Users FOREIGN KEY (UserID) REFERENCES dbo.Users(UserID),
        CONSTRAINT FK_UserRoles_Roles FOREIGN KEY (RoleID) REFERENCES dbo.Roles(RoleID)
    );
END
GO

IF OBJECT_ID('dbo.Permissions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Permissions (
        PermissionID INT IDENTITY(1,1) PRIMARY KEY,
        PermissionCode NVARCHAR(100) UNIQUE NOT NULL,
        PermissionName NVARCHAR(255) NOT NULL,
        Description NVARCHAR(MAX) NULL,
        CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

IF OBJECT_ID('dbo.RolePermissions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.RolePermissions (
        RoleID INT NOT NULL,
        PermissionID INT NOT NULL,
        PRIMARY KEY (RoleID, PermissionID),
        CONSTRAINT FK_RolePermissions_Roles FOREIGN KEY (RoleID) REFERENCES dbo.Roles(RoleID),
        CONSTRAINT FK_RolePermissions_Permissions FOREIGN KEY (PermissionID) REFERENCES dbo.Permissions(PermissionID)
    );
END
GO

IF OBJECT_ID('dbo.Modules', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Modules (
        ModuleID INT IDENTITY(1,1) PRIMARY KEY,
        ModuleCode NVARCHAR(100) UNIQUE NOT NULL,
        ModuleName NVARCHAR(255) NOT NULL,
        Description NVARCHAR(MAX) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

IF OBJECT_ID('dbo.Functions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Functions (
        FunctionID INT IDENTITY(1,1) PRIMARY KEY,
        ModuleID INT NOT NULL,
        FunctionCode NVARCHAR(100) UNIQUE NOT NULL,
        FunctionName NVARCHAR(255) NOT NULL,
        Description NVARCHAR(MAX) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_Functions_Modules FOREIGN KEY (ModuleID) REFERENCES dbo.Modules(ModuleID)
    );
END
GO

IF OBJECT_ID('dbo.PermissionFunctions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.PermissionFunctions (
        PermissionID INT NOT NULL,
        FunctionID INT NOT NULL,
        AssignedAt DATETIME NOT NULL DEFAULT GETDATE(),
        PRIMARY KEY (PermissionID, FunctionID),
        CONSTRAINT FK_PermissionFunctions_Permissions FOREIGN KEY (PermissionID) REFERENCES dbo.Permissions(PermissionID),
        CONSTRAINT FK_PermissionFunctions_Functions FOREIGN KEY (FunctionID) REFERENCES dbo.Functions(FunctionID)
    );
END
GO
