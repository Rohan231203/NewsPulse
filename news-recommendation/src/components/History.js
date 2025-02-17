import React from "react";
import { Typography, List, ListItem } from "@mui/material";

function History({ userId, history, fetchHistory }) {
  return (
    <div>
      <Typography variant="h6">Reading History</Typography>
      <List>
        {history.map((item, index) => (
          <ListItem key={index}>{item}</ListItem>
        ))}
      </List>
    </div>
  );
}

export default History;
