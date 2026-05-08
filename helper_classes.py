import numpy as np
epsilon = 1e-6
# This function gets a vector and returns its normalized form.
def normalize(vector):
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


# This function gets a vector and the normal of the surface it hit
# This function returns the vector that reflects from the surface
def reflected(vector, axis):
    # The furmula to the vector is : v - 2(v * n)n
    normal = normalize(axis)
    v = vector - 2 * (np.dot(vector, normal)) * normal
    return v

## Lights



# ====== Snell's law function =======

# This function gets a ray, the intersection point and the normal of the surface
# This function returns the ray that refracts from the surface
# Using Snell's Law: n1 * sin(theta1) = n2 * sin(theta2)
# n1 is the refractive index of the material the ray is coming from,
# and n2 is the refractive index of the material the ray is entering.
# theta1 is the angle between the normal and the ray before the refraction,
# and theta2 is the angle between the normal and the ray after the refraction.
# The function should return None if the refraction is impossible (total internal reflection)
def construct_refracted_ray(ray, intersection_point, normal, refractive_index=1.5):
    n1 = ray.refractive_index
    n2 = refractive_index if refractive_index != 0 else epsilon
    n_dot_v = np.dot(normal, ray.direction)
    ratio = n1 / n2
    k = np.sqrt(n_dot_v ** 2 + (1 / ratio) ** 2 - 1) - n_dot_v
    if k < 0:
        return None
    refracted_direction = ratio * (k * normal + ray.direction)
    return Ray(intersection_point, refracted_direction)



class LightSource:
    def __init__(self, intensity):
        self.intensity = intensity

    
class DirectionalLight(LightSource):

    def __init__(self, intensity, direction):
        super().__init__(intensity)
        self.direction = normalize(np.array(direction))

    # This function returns the ray that goes from the light source to a point
    def get_light_ray(self,intersection_point):
        dummy_origin = intersection_point - self.direction

        return Ray(dummy_origin, self.direction)

    # This function returns the distance from a point to the light source
    def get_distance_from_light(self, intersection):
        return np.inf

    # This function returns the light intensity at a point
    def get_intensity(self, intersection):
        return self.intensity


class PointLight(LightSource):
    def __init__(self, intensity, position, kc, kl, kq):
        super().__init__(intensity)
        self.position = np.array(position)
        self.kc = kc
        self.kl = kl
        self.kq = kq

    # This function returns the ray that goes from the light source to a point
    def get_light_ray(self, intersection):
        return Ray(self.position, normalize(intersection - self.position))

    # This function returns the distance from a point to the light source
    def get_distance_from_light(self,intersection):
        vector = intersection - self.position
        return np.linalg.norm(vector)

    # This function returns the light intensity at a point
    def get_intensity(self, intersection):
        # calculate distance between light source and intersection 
        # calculate and return the light intensity based on kc, kl, kq
        distance = self.get_distance_from_light(intersection)
        return self.intensity / (self.kc + (self.kl * distance) + self.kq * (distance**2))

class SpotLight(LightSource):
    def __init__(self, intensity, position, direction, kc, kl, kq):
        super().__init__(intensity)
        self.position = np.array(position)
        self.direction = normalize(direction)
        self.kc = kc
        self.kl = kl
        self.kq = kq

    # This function returns the ray that goes from the light source to a point
    def get_light_ray(self, intersection):
        return Ray(self.position, normalize(intersection - self.position))
        

    def get_distance_from_light(self, intersection):
        vector = intersection - self.position
        return np.linalg.norm(vector)

    def get_intensity(self, intersection):
        vector = normalize(intersection - self.position)
        distance = self.get_distance_from_light(intersection)
        return (self.intensity * (vector @ self.direction)) / (self.kc + (self.kl * distance) + self.kq * (distance**2))




class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction

    # The function is getting the collection of objects in the scene and looks for the one with minimum distance.
    # The function should return the nearest object and its distance (in two different arguments)
    def nearest_intersected_object(self, objects):
        nearest_object = None
        min_distance = np.inf
        #TODO: for all objects, check the intersection and pick the min t.
        for object in objects:
            hit = object.intersect(self)
            if hit is not None:
                t, intersected_object = hit
                if epsilon < t < min_distance:
                    min_distance = t
                    nearest_object = intersected_object

        return min_distance, nearest_object


class Object3D:
    def set_material(self, ambient, diffuse, specular, shininess, reflection):
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflection = reflection

    
    def intersect(self, ray:Ray):
        pass

class Plane(Object3D):
    def __init__(self, normal, point):
        self.normal = np.array(normal)
        self.point = np.array(point)

    def intersect(self, ray: Ray):
        v = self.point - ray.origin
        t = np.dot(v, self.normal) / (np.dot(self.normal, ray.direction) + epsilon)
        if t > 0:
            return t, self
        else:
            return None


class Triangle(Object3D):
    """
        C
        /\
       /  \
    A /____\ B

    The fornt face of the triangle is A -> B -> C.
    
    """
    def __init__(self, a, b, c):
        self.a = np.array(a)
        self.b = np.array(b)
        self.c = np.array(c)
        self.normal = self.compute_normal()

    # computes normal to the trainagle surface. Pay attention to its direction!
    def compute_normal(self):
        vector1 = self.b - self.a
        vector2 = self.c - self.a
        normal_vector = np.cross(vector1 , vector2)

        return normalize(normal_vector)

    def intersect(self, ray: Ray):
        v = self.a - ray.origin
        t = np.dot(v, self.normal) / (np.dot(self.normal, ray.direction) + epsilon)
        if t <= 0:
           return None
        point_on_the_plane = ray.origin + (t * ray.direction)

        triangle = [self.a, self.b, self.c]

        for i in range(3):
            v1 = triangle[i] - point_on_the_plane
            v2 = triangle[(i + 1) % 3] - point_on_the_plane
            product = np.cross(v1,v2)
            if (self.normal @ product) < 0:
                return None #It is outside the triangle
            
        return t, self



class Diamond(Object3D):
    """     
            D
            /\*\
           /==\**\
         /======\***\
       /==========\***\
     /==============\****\
   /==================\*****\
A /&&&&&&&&&&&&&&&&&&&&\ B &&&/ C
   \==================/****/
     \==============/****/
       \==========/****/
         \======/***/
           \==/**/
            \/*/
             E 
    
    Similar to Traingle, every from face of the diamond's faces are:
        A -> B -> D
        B -> C -> D
        A -> C -> B
        E -> B -> A
        E -> C -> B
        C -> E -> A
    """
    def __init__(self, v_list):
        self.v_list = v_list
        self.triangle_list = self.create_triangle_list()

    def create_triangle_list(self):
        l = []
        t_idx = [
                [0,1,3],
                [1,2,3],
                [0,3,2],
                [4,1,0],
                [4,2,1],
                [2,4,0]]
        # treat every triplet as a triangle face so 

        for idx in t_idx:

            # Grab the actual 3D points from v_list using the indices
            p1 = self.v_list[idx[0]]
            p2 = self.v_list[idx[1]]
            p3 = self.v_list[idx[2]]

            face = Triangle(p1,p2,p3)
            l.append(face)

        return l

    def apply_materials_to_triangles(self):
        for triangle in self.triangle_list:
            triangle.set_material(
                self.ambient,
                self.diffuse,
                self.specular,
                self.shininess,
                self.reflection
            )

    def intersect(self, ray: Ray):
        nearest_face = None
        min_distance = np.inf

        for triangle in self.triangle_list:
            hit = triangle.intersect(ray)
            if hit is not None:
                t, intersected_object = hit
                if epsilon < t < min_distance:
                    min_distance = t
                    nearest_face = intersected_object

        #If we hit nothing
        if nearest_face is None:
            return None
        
        return  min_distance, nearest_face


class Sphere(Object3D):
    def __init__(self, center, radius: float):
        self.center = np.array(center)
        self.radius = radius

    def intersect(self, ray: Ray):
        ray_vector = ray.origin - self.center

        #Calculate the coefficients of the quadratic equation after substitute the vector equation in sphere
        a = ray.direction @ ray.direction
        b = 2.0 * (ray.direction @ ray_vector)
        c = (ray_vector @ ray_vector) - (self.radius ** 2)

        # Calculate the discriminant
        discriminant = (b ** 2) - (4 * a * c)
        if discriminant < 0:
            return None # No intersection
        sqrt = np.sqrt(discriminant)
        intersection_point1 = (-b - sqrt) / (2 * a)
        intersection_point2 = (-b + sqrt) / (2 * a)

        # Since point1 is calculated with subtraction, it will always be smaller than point2. 
        if intersection_point1 > epsilon:
            return intersection_point1, self
        
        if intersection_point2 > epsilon:
            return intersection_point2, self
        
        # If both are negative, the entire sphere is behind the camera
        return None