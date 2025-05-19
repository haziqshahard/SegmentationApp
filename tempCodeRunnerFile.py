                    def expand_polygon(points, pixel_expansion):
                        centroid = get_centroid(points)
                        
                        # Create a new set of vertices, each one moved outward by the given number of pixels
                        new_points = []
                        for point in points:
                            # Calculate the vector from the centroid to the point
                            vector = (point[0] - centroid[0], point[1] - centroid[1])
                            
                            # Normalize the vector
                            vector_length = distance(centroid, point)
                            if vector_length != 0:
                                unit_vector = (vector[0] / vector_length, vector[1] / vector_length)
                            else:
                                unit_vector = (0, 0)
                            
                            # Expand the point by the fixed number of pixels along the direction of the unit vector
                            new_point = (
                                point[0] + unit_vector[0] * pixel_expansion, 
                                point[1] + unit_vector[1] * pixel_expansion
                            )
                            new_points.append(new_point)
                        
                        return new_points