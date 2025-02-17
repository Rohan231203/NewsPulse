import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Container, Grid, Typography, Box, Button, CircularProgress, Snackbar } from "@mui/material";
import Recommendations from "./components/Recommendations";
import History from "./components/History";
import MarkRead from "./components/MarkRead";

function App() {
  const [userId] = useState("user_123");
  const [recommendations, setRecommendations] = useState([]);
  const [readArticles, setReadArticles] = useState([]);
  const [userHistory, setUserHistory] = useState([]);
  const [recommendationPage, setRecommendationPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ✅ Fetch recommendations
  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/recommendations/", {
        user_id: userId,
        user_read_articles: readArticles,
        page: recommendationPage,
      });

      console.log("API Response:", response.data); // Debugging

      if (Array.isArray(response.data.articles)) {
        setRecommendations(response.data.articles);
      } else {
        throw new Error("Invalid response format");
      }
    } catch (err) {
      setError("Error fetching recommendations");
      console.error("Fetch Recommendations Error:", err);
    } finally {
      setLoading(false);
    }
  }, [userId, readArticles, recommendationPage]);

  // ✅ Fetch recommendations on page load and update when recommendationPage changes
  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations, recommendationPage]);

  // ✅ Fetch user history once
  useEffect(() => {
    axios
      .post("http://localhost:8000/user_history", { user_id: userId })
      .then((response) => setUserHistory(response.data.history))
      .catch((error) => {
        setError("Error fetching user history");
        console.error("User History Error:", error);
      });
  }, [userId]);

  // ✅ Mark an article as read
  const handleMarkRead = async (articleLink) => {
    if (!readArticles.includes(articleLink)) {
      setReadArticles((prev) => [...prev, articleLink]);
      try {
        await axios.post("http://localhost:8000/mark_read", {
          user_id: userId,
          article_link: articleLink,
        });
        fetchRecommendations();
      } catch (error) {
        setError("Error marking article as read");
        console.error("Mark Read Error:", error);
      }
    }
  };

  // ✅ Clear user history
  const clearHistory = async () => {
    try {
      await axios.post("http://localhost:8000/clear_history", { user_id: userId });
      setUserHistory([]); // Clear UI history
      console.log("User history cleared");
    } catch (error) {
      setError("Error clearing user history");
      console.error("Clear History Error:", error);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h3" align="center" gutterBottom>
        News Article Recommendation
      </Typography>

      <Grid container spacing={3}>
        {/* History Section */}
        <Grid item xs={12} md={4}>
          <History userId={userId} history={userHistory} />
          <Button variant="outlined" color="secondary" onClick={clearHistory} sx={{ mt: 2 }}>
            Clear History
          </Button>
        </Grid>

        {/* Recommended Articles Section */}
        <Grid item xs={12} md={8}>
          <Typography variant="h5" gutterBottom>
            Recommended Articles
          </Typography>
          <Grid container spacing={2}>
            {recommendations.map((article, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <MarkRead article={article} onMarkRead={handleMarkRead} />
              </Grid>
            ))}
          </Grid>
          <Button
            variant="contained"
            color="primary"
            onClick={() => setRecommendationPage((prev) => prev + 1)}
            disabled={loading}
            sx={{ mt: 2 }}
          >
            Load More
          </Button>
        </Grid>
      </Grid>

      {/* Loading Indicator */}
      {loading && (
        <Box display="flex" justifyContent="center" mt={2}>
          <CircularProgress />
        </Box>
      )}

      {/* Error Snackbar */}
      <Snackbar
        open={Boolean(error)}
        autoHideDuration={6000}
        onClose={() => setError("")}
        message={error}
      />
    </Container>
  );
}

export default App;
