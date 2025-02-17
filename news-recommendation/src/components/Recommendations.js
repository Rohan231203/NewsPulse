import React from "react";
import { Card, CardContent, Typography, Button } from "@mui/material";

function Recommendations({ recommendations }) {
  return (
    <div>
      <Typography variant="h5" gutterBottom>
        Recommended Articles
      </Typography>
      {recommendations.map((rec) => (
        <Card key={rec.id} sx={{ maxWidth: 345, marginBottom: 2 }}>
          <CardContent>
            <Typography variant="h6">{rec.title}</Typography>
            <Typography variant="body2" color="text.secondary">
              {rec.description}
            </Typography>
            <Button size="small" color="primary" href={rec.url} target="_blank">
              Read More
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default Recommendations;
