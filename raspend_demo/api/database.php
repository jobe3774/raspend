<?php

class Database 
{
  // Lokale Einstellungen
  
  private $db_name  = "raspend_demo";
  private $host     = "localhost";
  private $username = "root";
  private $password = "";

  // Entfernte Einstellungen
  /*
  private $db_name  = "";
  private $host     = "";
  private $username = "";
  private $password = "";
  */
  
  public $conn;

  // get the database connection
  public function getConnection() 
  {

    $this->conn = null;

    try 
    {
      $this->conn = new PDO("mysql:host=" . $this->host . ";dbname=" . $this->db_name, $this->username, $this->password);
      $this->conn->exec("set names utf8");
    } 
    catch (PDOException $exception) 
    {
      echo "Connection error: " . $exception->getMessage();
    }

    return $this->conn;
  }
}
