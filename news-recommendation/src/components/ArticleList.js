import React from "react";
import { Card, CardContent, Typography, Button } from "@mui/material";

function ArticleList({ article }) {
  return (
    <Card sx={{ maxWidth: 345 }}>
      <CardContent>
        <Typography variant="h6" component="div">
          {article.title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {article.description}
        </Typography>
        <Button size="small" color="primary" href={article.url} target="_blank">
          Read More
        </Button>
      </CardContent>
    </Card>
  );
}

export default ArticleList;
