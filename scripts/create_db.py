"""To create the DB for the app"""

import inspect
import os
import MySQLdb as sql
import sys


here = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(os.path.join(here, os.pardir))

import config as cfg

create_query = "CREATE DATABASE IF NOT EXISTS `{0}`;".format(cfg.db)

query = """-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Aug 20, 2015 at 08:59 PM
-- Server version: 5.5.44-0ubuntu0.14.04.1
-- PHP Version: 5.5.9-1ubuntu4.11

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `{0}`
--

-- --------------------------------------------------------

--
-- Table structure for table `annotations`
--

CREATE TABLE IF NOT EXISTS `annotations` (
  `menId` varchar(255) NOT NULL,
  `eLabel` varchar(255) NOT NULL,
  `annotator` enum('aida','babelfy','spotlight','tagme','wminer') NOT NULL,
  `confidence` float NOT NULL,
  `active` tinyint(4) NOT NULL,
  PRIMARY KEY (`menId`,`annotator`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `corpora`
--

CREATE TABLE IF NOT EXISTS `corpora` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sname` varchar(255) NOT NULL,
  `lname` varchar(255) NOT NULL,
  `type` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `documents`
--

CREATE TABLE IF NOT EXISTS `documents` (
  `id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `totalPages` int(11) NOT NULL DEFAULT '1',
  `corpusId` int(11) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `speaker` varchar(255) NOT NULL,
  `author` varchar(255) NOT NULL,
  `subdoc` varchar(255) NOT NULL,
  `turnnbr` int(11) NOT NULL COMMENT 'useful to identify a stretch of document in connection with a speaker',
  `text` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `entities`
--

CREATE TABLE IF NOT EXISTS `entities` (
  `eLabel` varchar(255) NOT NULL,
  `eType` enum('PER','ORG','LOC','TCO','COD','NOE') NOT NULL,
  PRIMARY KEY (`eLabel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `mentions`
--

CREATE TABLE IF NOT EXISTS `mentions` (
  `menId` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `menStr` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `start` int(11) NOT NULL,
  `end` int(11) NOT NULL,
  `docId` varchar(255) NOT NULL,
  `subdoc` varchar(255) NOT NULL,
  `sentNbr` int(11) NOT NULL,
  PRIMARY KEY (`menId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
""".format(cfg.db)


def main():
    """Create DB and its tables based on query in this module"""
    con = sql.connect(cfg.host, cfg.user, cfg.pw)
    cur = con.cursor()
    cur.execute(create_query)
    cur.close()
    con2 = sql.connect(cfg.host, cfg.user, cfg.pw, cfg.db)
    cur2 = con2.cursor()
    cur2.execute(query)
    cur2.close()


if __name__ == "__main__":
    main()