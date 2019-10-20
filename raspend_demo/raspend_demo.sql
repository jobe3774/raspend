-- phpMyAdmin SQL Dump
-- version 4.8.2
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Erstellungszeit: 20. Okt 2019 um 14:31
-- Server-Version: 10.1.34-MariaDB
-- PHP-Version: 7.2.8

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `raspend_demo`
--
CREATE DATABASE IF NOT EXISTS `raspend_demo` DEFAULT CHARACTER SET utf8 COLLATE utf8_bin;
USE `raspend_demo`;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `temperatures`
--

DROP TABLE IF EXISTS `temperatures`;
CREATE TABLE `temperatures` (
  `id` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `basement.party_room` float DEFAULT NULL,
  `basement.fitness_room` float DEFAULT NULL,
  `basement.heating_room` float DEFAULT NULL,
  `groundfloor.kitchen` float DEFAULT NULL,
  `groundfloor.living_room` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `temperatures`
--
ALTER TABLE `temperatures`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `temperatures`
--
ALTER TABLE `temperatures`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
