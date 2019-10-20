<?php
include_once './database.php';

$contents = file_get_contents('php://input');
$temperatures = json_decode($contents);

$database = new Database();
$db = $database->getConnection();

$insertStmt = "INSERT INTO temperatures (`basement.party_room`," . 
                                       " `basement.fitness_room`," . 
                                       " `basement.heating_room`," . 
                                       " `groundfloor.kitchen`, ". 
                                       " `groundfloor.living_room`)" . 
              " VALUES (?, ?, ?, ?, ?);";

$stmt = $db->prepare($insertStmt);

$succeeded = $stmt->execute(array($temperatures->basement->party_room, 
                                  $temperatures->basement->fitness_room, 
                                  $temperatures->basement->heating_room, 
                                  $temperatures->ground_floor->kitchen, 
                                  $temperatures->ground_floor->living_room));

$newID = -1;
$errMsg = "";

if ($succeeded)
{
  $newID = $db->lastInsertId();
}
else
{
  $errMsg = $stmt->errorInfo()[2];
}

$dbResult = array("lastInsertId" => $newID, "errorMessage" => $errMsg);
$json = json_encode($dbResult);

header('Content-Type: application/json');
echo $json;
  
exit();
?> 