import React from "react";
import { Card, CardContent, Typography, Button } from "@mui/material";

const MarkRead = ({ article, onMarkRead }) => {
  return (
    <Card variant="outlined" sx={{ mb: 2, p: 2, borderRadius: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {article.headline}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {article.summary}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          sx={{ mt: 1 }}
          onClick={() => onMarkRead(article.link)}
        >
          Mark as Read
        </Button>
      </CardContent>
    </Card>
  );
};

export default MarkRead;
